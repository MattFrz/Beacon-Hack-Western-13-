# micd — C270 webcam mic capture on QNX 8 (work in progress)

User-space USB Audio Class (UAC1) capture driver for the Logitech C270
webcam's built-in mic on the QNX 8 QSTI image (Raspberry Pi 5). It exists
because the stock audio stack on this image cannot create a capture PCM
for the C270 (see `docs/pi-bringup.md`, "Webcam mic, stock path" —
`ado_pcm_create_internal: PCM devices are required to support BLOCK_
TRANSFER mode`), so `arecord`/`waverec` have nothing to open.

`micd` bypasses `io-snd` entirely and talks to `io-usb-otg` through
`libusbdi`, the same connection model as QNX's own sensor-framework USB
camera driver.

## Build and run (on the Pi)

```sh
sudo -n apk add qnx-usb-dev        # one-time: installs sys/usbdi.h etc.
cc -O2 micd.c -o micd -lusbdi
sudo -n ./micd -t 5 -o /tmp/mic.wav          # 48 kHz 16-bit mono WAV
```

Useful options:

- `-a alt`  alt setting on the AudioStreaming interface
  (C270: 1=16k 2=24k 3=32k 4=48k; default 4)
- `-t secs` duration (0 = until killed), `-o file` output WAV
- `-v`      dump insertions, descriptors, first frames
- `-c`      diagnostic camera mode: stream the C270's **video** endpoint
  (iface 1, alt 11) with the same URB code — used to prove the host iso
  path works (see status below). Slays the sensor service first if you
  want to try it, since only one driver can claim the video interfaces.
- `-n N -u M` iso frames per URB / URBs in flight
- `-m 1` plain `usbd_setup_isochronous` mode, `-F N` explicit stream
  start frame, `-R 0` don't re-setup URBs on resubmit (leaks TRBs)

## Status

**Verdict (2026-11-22): root-caused to the closed QNX dwc3-xhci driver; not fixable from user space.**

Everything up to the isochronous stream works: per-interface insertion
callbacks, claiming only the AudioStreaming interface (the sensor
framework keeps the camera), FORMAT_TYPE parsing, alt selection,
feature-unit unmute and endpoint sample-rate `SET_CUR` — all ACKed by
the device.

The audio endpoint is **never serviced by the controller**. Forensics
via direct MMIO on the live stack (probe tools archived in
`forensics/`; recipe in `docs/pi-bringup.md`):

- The EP gets a well-formed ring — real ISOCH TRBs (type 5, chained
  100-byte buffers, SIA+IOC), Running state, correct interval — but
  the controller's dequeue **never advances a single TRB**, ever.
- The ~1008/s "completions" micd receives (status 0, len 0) are
  **fabricated by the driver's software path**: the command-ring
  history shows it cycling `Configure Endpoint` / `Stop Endpoint` /
  `Set TR Dequeue Pointer` for DCI 13 and issuing `drop DCI 13`
  commands.
- User-space interventions, all ineffective: ringing the EP doorbell
  with valid TRBs queued; patching `EPType=5` into the live context;
  flipping TRB cycle bits to match DCS; appending a Configure Endpoint
  command in both spec and driver encoding (that one just stalls the
  driver's simulator). A context reload needs a command-ring slot, and
  the driver's retry loop keeps that ring hot.
- Decisive control: `micd -c` streams the C270's **video** endpoint
  (`bInterval` 1 = one microframe period) and its dequeue visibly
  advances — µframe-period iso is genuinely hardware-scheduled. Only
  the 1 ms service period (high-speed bInterval 4) is simulated away.
  **Every USB audio device uses bInterval 4** — a headset or dongle
  would fail identically; different USB hardware is not a workaround
  on this image.

Together with the io-snd BLOCK_TRANSFER failure these are two
reproducible QSTI audio-capture bugs — QNX-foundry/mentor report
material. The fix must come from a `devu-hcd-dwc3-xhci` package update
(the `-dbg` apk ships symbols but the same code).

Working microphone input on this board: **Bluetooth HFP capture**
(btstack over the onboard BCM UART, `hfp_ag_auto`) — documented in
`docs/pi-bringup.md`.

## Gotchas learned the hard way

- Resubmits must re-run `usbd_setup_isochronous_stream()` before every
  `usbd_io()`, or the XHCI endpoint ring leaks TRBs
  (`xring_add_streaming_isoch_xfer: out of TRBs`).
- The pipe must be opened **after** `usbd_select_interface()` picks the
  alt setting; at alt 0 the endpoint has no XHCI ring.
- QNX `getopt` mis-parses a no-argument flag that immediately follows a
  colon'd option in the optstring (e.g. `"R:r:v"`) — keep flags at the
  front of the string.
- If `io-usb-otg` ever dies: `sudo -n sh /usr/etc/usb_start.sh` restores
  it. A soft reboot does **not** power-cycle the webcam; to truly reset
  the C270, drop VBUS with `sudo -n gpio-rp1 set 42 op pn dl`, wait ~5 s,
  restore with `set 42 a2 pn; set 43 a2 pu` (may require restarting
  io-usb-otg and `sensor` afterwards).
