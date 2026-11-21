# Pi development workflow - QNX 8.0 on Raspberry Pi 5

How to build, deploy, debug and recover the chest-worn Pi. Product, geometry,
and QNX contracts live in [`nathans-revision.md`](nathans-revision.md); this
file is the on-device loop only. Everything here was verified against the
running device, not copied from generic advice.

The device is not a normal Linux box. It boots a **read-only IFS image**, keeps
state on a **QNX6 data partition**, and has **no systemd, no apt, no bash
guarantees**. Most of the traps below come from those three facts.

---

## 1. The loop you actually run

```sh
ssh qnxpi                                  # key auth, no password
rsync -az --delete ./app/ qnxpi:/data/home/qnxuser/app/
ssh qnxpi 'cd /data/home/qnxuser/app && make && ./run.sh'
ssh qnxpi 'slog2info -w'                   # follow logs
```

Restart one process without rebooting:

```sh
ssh qnxpi 'slay -f myproc; cd /data/home/qnxuser/app && ./myproc &'
```

Reboot the target:

```sh
ssh qnxpi 'sudo -n shutdown -r now'        # or just power-cycle
```

---

## 2. Access

| Thing | Value |
|---|---|
| Host | `ssh qnxpi` → `qnxuser@10.80.55.25` |
| Auth | key (`~/.ssh/id_ed25519`), installed in `/home/qnxuser/.ssh/authorized_keys` |
| Privilege | `qnxuser` is in `sudo`; `sudo -n` works without a password |
| Hostname | `qnxpi` - hardcoded by `setconf _CS_HOSTNAME qnxpi` in `slm.cfg` |
| Wi‑Fi MAC | `88:a2:9e:a9:d4:d4` |
| Network | `cybernet` phone hotspot, `10.80.55.0/24`, gw `10.80.55.90` |

**The alias is IP-pinned** (`/etc/nixos/home/nate/ssh.nix`). mDNS does not work
reliably on the laptop: `avahi-resolve-host-name -4 qnxpi.local` returns the
right address, but glibc never sees it - `systemd-resolved` reports per-link
`-mDNS`, the `nss-mdns` module fails to load, and `qnxpi.local` then falls
through the `home.lab` search domain and resolves to an unrelated tailnet host.
If the lease changes, read it off the Pi with `ifconfig bcm0` and update the
alias.

Set a real password before demo day - `passwd` must be run **interactively** on
the device (piping into `ssh -tt` does not work; it hangs at `Old Password:`):

```sh
ssh qnxpi      # then, on the device:
passwd         # current password is the factory default: qnxuser
```

Until you do, anyone on the hotspot can log in as `qnxuser` (and `sudo` to root).

---

## 3. Where things live

| Path | What | Survives reboot | Survives reflash |
|---|---|---|---|
| `/` | IFS image (`/boot/qnx_sdp.ifs`), read-only | n/a | yes |
| `/data` | QNX6 partition, 19 GB, ~17 GB free | **yes** | **no** |
| `/boot` | FAT boot partition, visible on a PC | yes | no |
| `/usr` (`/system`) | QNX6 system partition; `/etc` → `/system/etc` | yes | no |
| `/dev/shmem` | RAM, lost on reboot | no | - |

**Put your code in `/data`.** It is the only large writable space and it is where
`/home` lives (`/home` → `/data/home`, so `/home/qnxuser` = `/data/home/qnxuser`).

`/etc` being a symlink to `/system/etc` means editing config feels permanent, but
it lives on the *system* partition - a reflash wipes it, and it is shared with
QNX's own files. Prefer `/data` for anything you own.

The IFS itself cannot be rebuilt here: that needs `mkifs` from the QNX SDP, which
this host does not have. Treat `qnx_sdp.ifs` as immutable.

---

## 4. Deploying code

The device has a real toolchain - `gcc`, `make`, `git`, `python3.14`, `pip3`,
`rsync`, `scp`, `ssh`, and `python3 -m venv` works.

Two viable loops:

**Build on the device** (simplest, and what the above assumes). `rsync` the tree,
run `make` over SSH. Fast enough for a hackathon and avoids cross-toolchain setup.

**Cross-build on the host.** Only worth it if build times start hurting; it needs
a QNX SDP toolchain on the NixOS side, which is not configured today.

Because the device has `pip3` but the hotspot may be the only uplink, prefer
`rsync`-ing a pre-populated `venv` or pure-Python deps over installing at demo
time. Verify a clean `pip3 install` still works before you rely on it.

---

## 5. QNX process and logging idioms

There is no systemd. Use these instead:

| Need | Do |
|---|---|
| List processes | `pidin ar` |
| Kill / restart one | `slay -f <name>` |
| Follow logs | `slog2info -w` |
| Filter logs | `slog2info -b <buffer>` |
| Check an interface | `ifconfig bcm0` |
| Check routes | `netstat -rn` |

To make a process survive your SSH session, detach it - `nohup`-style shell
backgrounding is fine, but a process started from an SSH session dies when the
session closes unless it is genuinely detached. Simplest reliable pattern for
demo: start `supervisor` from a snippet after `io-audio`, Sensor Framework,
and `/usr` (QSTI `post_startup` / an SLM component ordered after those). Do
**not** launch Beacon from `/boot/onboot` - that script runs before pipes and
`/usr` exist (spec §5.1). `/boot/onboot` stays for Wi-Fi and hostname only.

`slogger2` writes to per-buffer logs; `slog2info` reads them. If a process exits
instantly, `slog2info` usually says why within a couple of seconds - check there
before adding print statements.

---

## 6. Boot-time customisation (`/boot/onboot`)

`mount_fs.sh` (SLM component `root-fs`) mounts the FAT partition at `/boot`, then:

```sh
if [ -e /boot/onboot ]; then
    echo Running onboot script
    ksh /boot/onboot
fi
```

This is the only supported hook that runs **before** the network comes up. It is
how you make config changes take effect on the *same* boot. Two hard constraints,
both learned the hard way:

### No pipes

`onboot` runs before the SLM `pipe` component starts. `$(...)`, backticks and
`a | b` all fail with:

```
/boot/onboot[25]: can't create pipe - try again
```

Use redirection to files and exit codes instead:

```sh
# instead of: pidin ar | grep wpa_supplicant
pidin ar >/dev/shmem/pidin.txt 2>&1
if grep -q wpa_supplicant /dev/shmem/pidin.txt; then ...

# instead of: echo "date is $(date)"
date
```

### Only `/proc/boot` exists

`mount_fs.sh` mounts the system partition at `/usr` **after** `onboot` returns, so
most utilities are missing. `cp`, `chown`, `sync` and `date` all fail with
`cannot execute - No such file or directory`. What you *do* have is the small
`/proc/boot` set: `cat`, `ls`, `mount`, `umount`, `mkdir`, `chmod`, `sleep`, `sh`.

```sh
# instead of: cp /boot/wpa_supplicant.conf /data/var/etc/settings/
cat /boot/wpa_supplicant.conf >/data/var/etc/settings/wpa_supplicant.conf
```

Anything that needs pipes, `/usr` or shell utilities should go in a **background
child** that sleeps past the boot (`sleep 45; ...) &`) - by then both exist.

### Write diagnostics to `/boot`

`/boot` is a writable FAT partition, so the device can leave its own logs where a
PC can read them - no serial console needed:

```sh
exec >>/boot/onboot.log 2>&1
```

Log anything that matters, especially on the boot path. You cannot attach a debugger
to a boot that already failed.

---

## 7. Network configuration

Wi‑Fi settings are read at boot from **`/data/var/etc/settings/`**, not from
`/boot`:

| File | Contents |
|---|---|
| `wpa_supplicant.conf` | `ssid`, `key_mgmt=WPA-PSK`, `psk` |
| `network` | `HOSTNAME=`, `IP_ADDR=`, `TIME_SERVERS=` |

`/boot/wpa_supplicant.conf` and `/boot/network` are the *provisioning* copies.
QNX copies them onto `/data` **only when the `/boot` copy is newer**
([`cti/boot.html`](https://www.qnx.com/developers/docs/qnxeverywhere/com.qnx.doc.target_images/topic/cti/boot.html)).

That timestamp gate has a known bug, **QNXE‑1894**:

> Wi‑Fi settings added to `/boot/wpa_supplicant.conf` after the initial boot may
> not be copied to `/data/var/etc/settings/wpa_supplicant.conf`, preventing Wi-Fi
> from connecting. **Workaround:** Manually copy the `wpa_supplicant.conf` file
> from `/boot/` to `/data/var/etc/settings/`.

The symptom is nasty: `bcm0` reports `status: associated` but sits on a
`169.254.x.x` link-local address with no default route, and the device is simply
absent from the network. Check with `ifconfig bcm0` and `netstat -rn`.

The fix used here is the `onboot` hook in §6: `cat` the `/boot` copies into
`/data/var/etc/settings/` on every boot, which bypasses the gate entirely.

Keep `/boot` timestamps in the future for these two files so the built-in copy
also fires as a second line of defence:

```sh
touch -d '2030-01-01 00:00:00' /path/to/mounted/boot/{wpa_supplicant.conf,network}
```

`IP_ADDR` is **Ethernet-only** - it does nothing for Wi‑Fi, which always gets its
address from `dhcpcd` on `bcm0`.

Other facts worth having: the Wi‑Fi interface is **`bcm0`** (not `wlan0`), driven
by `wpa_supplicant -D qwdi -i bcm0`; and every RPi5 ships the same default Wi‑Fi
MAC in its NVRAM, which can block DHCP when several are on one network
(**QNXE‑2016**). This unit is `88:a2:9e:a9:d4:d4`, so it is not affected.

---

## 8. SD card workflow

**Use a USB card reader. Do not use the laptop's internal slot.**

The internal `rtsx_pci` reader on this machine drops its PCIe link within a minute
or two of boot:

```
pcieport 0000:00:1c.0: broken device, retraining non-functional downstream link at 2.5GT/s
pcieport 0000:00:1c.0: retraining failed
mmc0: error -110 doing runtime resume
```

After that the card is unreadable until a **cold boot** - `pci rescan`, unbind/rebind
and bridge resets all fail to bring it back. With a USB reader there is none of
this: the card appears as `/dev/sdX` and stays usable.

```sh
lsblk                                   # identify: the 800M vfat partition is /boot
udisksctl mount -b /dev/sda1
M=$(lsblk -no MOUNTPOINT /dev/sda1)

install -m 0644 staged/wpa_supplicant.conf "$M/"
install -m 0755 staged/onboot             "$M/"
touch -d '2030-01-01 00:00:00' "$M/wpa_supplicant.conf" "$M/network"

# FAT + ksh: CRLF breaks the script. Verify zero carriage returns.
grep -c $'\r' "$M/onboot"        # must print 0

sync && udisksctl unmount -b /dev/sda1
```

The boot partition also contains three leftover files from a previous Raspberry
Pi OS install - `user-data`, `network-.con`, `cmdline.txt` with a Linux mac80211
regulatory setting. They are inert for QNX; do not "fix" them.

---

## 9. Diagnostics ladder

When the Pi does not appear on the network, work down this list before guessing:

1. **Is it on the hotspot?** Check the phone's client list for `88:a2:9e:a9:d4:d4`.
2. **Does it have a lease?** `ifconfig bcm0` - `169.254.x.x` means association
   without DHCP (usually stale settings, §7).
3. **Did the boot hook run?** Read `/boot/onboot.log` from the card on a PC.
   A 49-byte log containing `can't create pipe` means §6 was violated.
4. **Is the supplicant alive?** `pidin ar | grep wpa` over SSH, or
   `/boot/watchdog.log`.
5. **Serial console** as the last resort: `enable_uart=1` is set in `config.txt`,
   `devc-serpl011-rpi5` runs at `115200` on the 40-pin header, and `tty-login.sh`
   gives a login prompt. Wire USB‑TTL to **pin 8 (TX), pin 10 (RX), pin 6 (GND)** -
   this shows the full boot, including everything `onboot` cannot log.

---

## 10. Trap list

| Symptom | Cause |
|---|---|
| `can't create pipe - try again` | pipe/process substitution in a pre-`pipe` boot hook (§6) |
| `cp: cannot execute` at boot | `/usr` not mounted yet; use `cat >` (§6) |
| `bcm0` associated, `169.254.x.x` | QNXE‑1894; settings never reached `/data` (§7) |
| Card vanishes after a minute | internal `rtsx_pci` reader; use USB (§8) |
| `onboot` script ignored | CRLF line endings from a FAT round-trip (§8) |
| `qnxpi.local` resolves to a tailnet IP | mDNS fallthrough to `home.lab` (§2) |
| `ssh` connects then fails to negotiate | QNXE‑195; add `HostKeyAlgorithms=+ssh-rsa` |
| `df` shows `/` tiny | `/` is the in-memory IFS; `/data` is the real disk (§3) |

---

## 11. Before demo

- [ ] `passwd` set on the device (§2)
- [ ] Code lives under `/data`, not `/etc` or `/system`
- [ ] Processes start from a boot hook or explicit script, not your SSH session
- [ ] `slog2info` checked, not just stdout
- [ ] Card flashed from a **USB** reader, `grep -c $'\r'` returns 0
- [ ] Cold-boot tested end to end - not just `slay` + restart
- [ ] Spare card flashed and labeled
