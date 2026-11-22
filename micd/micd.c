/*
 * micd - capture audio from a USB Audio Class (UAC1) microphone, e.g. the
 * Logitech C270 webcam's built-in mic, on QNX 8 (Raspberry Pi 5 QSTI).
 *
 * Why this exists: the stock io-snd / sndrv-ctrl-usb.so stack enumerates the
 * C270's audio interfaces fine but dies with
 *   "PCM devices are required to support BLOCK_TRANSFER mode"
 * when building the capture PCM node (capture-only device; QNXE image bug),
 * so /dev/snd never gets a pcmC*c device and arecord/waverec have nothing to
 * open.  micd bypasses io-snd entirely: it talks to io-usb-otg via libusbdi,
 * claims the AudioStreaming interface, selects an alternate setting (which
 * fixes the sample rate on the C270), and streams isochronous IN packets to a
 * WAV file.  Same libusbdi connection model as the QNX USB driver docs and
 * llmike/devu-uvc (the reference for isoch streaming on QNX).
 *
 * Usage:
 *   micd [-a alt] [-t secs] [-o out.wav] [-p usb-path] [-v] [vid did]
 *     -a alt     alternate setting on the AudioStreaming interface
 *                (C270: 1=16k 2=24k 3=32k 4=48k; default 4)
 *     -t secs    record duration (default 5; 0 = until killed)
 *     -o file    output WAV (default /tmp/mic.wav)
 *     -p path    io-usb server path (default: stack default, then
 *                /dev/usb/io-usb-otg)
 *     -v         verbose: dump insertions, descriptors, first frames
 *     vid did    hex USB vendor/product IDs to match (default 046d 0825)
 *
 * Build (on the Pi, with qnx-usb-dev installed for <sys/usbdi.h>):
 *   cc -O2 micd.c -o micd -lusbdi
 *
 * Run as root (USB stack access):
 *   sudo -n ./micd -t 5 -o /tmp/mic.wav -v
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdarg.h>
#include <unistd.h>
#include <time.h>
#include <errno.h>

#include <sys/usbdi.h>

/* ---- tunables -------------------------------------------------------- */

#define N_URBS      3
#define N_FRAMES    16          /* iso service intervals per URB; keep the
                                 * in-flight TRB count well under the
                                 * XHCI endpoint ring size (64-frame URBs
                                 * hit "out of TRBs" on this stack)      */
#define MAX_URBS    8           /* array cap; -u may not exceed this     */
#define USB_CLASS_AUDIO       0x01
#define USB_SUBCLASS_AUDIOCTL 0x01
#define USB_SUBCLASS_AUDIOSTR 0x02

/* ---- state ------------------------------------------------------------ */

static struct usbd_connection *g_conn;
static struct usbd_device    *g_dev;         /* handle scoped to AS iface  */
static struct usbd_device    *g_dev_ac;      /* AudioControl iface handle  */
static struct usbd_pipe      *g_pipe;
static struct usbd_pipe      *g_ctl;         /* EP0 control pipe            */
static int      g_ep_addr;                   /* iso IN endpoint address     */
static struct usbd_urb       *g_urbs  [MAX_URBS];
static uint8_t               *g_bufs  [MAX_URBS];
static usbd_isoch_frame_request_t *g_flist[MAX_URBS];

static int      g_n_frames = N_FRAMES, g_n_urbs = N_URBS;
static int      g_vid = 0x046d, g_did = 0x0825;
static int      g_alt = 4, g_secs = 5, g_verbose = 0;
static int      g_payload;                   /* wMaxPacketSize             */
static int      g_as_iface = -1;             /* AudioStreaming iface no.   */
static int      g_rate = 48000, g_chans = 1, g_bits = 16;
static FILE    *g_out;
static const char *g_outpath = "/tmp/mic.wav";

static volatile long  g_bytes;
static volatile int   g_frames_ok, g_frames_err, g_stalled;
static int      g_mode;                    /* 0 = iso stream, 1 = plain iso */
static int      g_resetup = 1;              /* re-setup URB before resubmit  */
static int      g_devreset;                /* -e: port-reset the device      */
static int      g_cammode;                 /* -c: stream the VIDEO endpoint  */
static int      g_frame_off;               /* -f: schedule at cur frame + N  */
static int      g_sframe_off;              /* -F: stream sframe = cur + N     */
static volatile int   g_insert_seen, g_stream_started, g_done, g_failed;

static struct timespec g_t0;

static void submit_plain(int id);
static void completion(struct usbd_urb *urb, struct usbd_pipe *pipe,
                       void *handle);
static double now_elapsed(void);

/* ---- helpers --------------------------------------------------------- */

static void logf_(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fflush(stderr);
}

#define VLOG(...)  do { if (g_verbose) logf_(__VA_ARGS__); } while (0)

static usbd_descriptors_t *desc_at(struct usbd_device *d,
                                  struct usbd_desc_node *root,
                                  int type, int index,
                                  struct usbd_desc_node **node)
{
    if (root == NULL)
        return NULL;
    return usbd_parse_descriptors(d, root, type, index, node);
}

/* Find the AS interface's isochronous IN endpoint at the requested alt
 * setting.  Fills g_rate/g_chans/g_bits/g_payload and opens the pipe.
 * `iface` is the AudioStreaming interface number from the insertion. */
static int find_audio_stream(struct usbd_device *d, int config, int iface)
{
    struct usbd_desc_node *ni, *ne;
    usbd_interface_descriptor_t *ifd;
    int k;

    ifd = usbd_interface_descriptor(d, config, iface, g_alt, &ni);
    if (ifd == NULL) {
        logf_("micd: no iface %d alt %d descriptor\n", iface, g_alt);
        return -1;
    }
    VLOG("  AS iface %d alt %d: class %02x.%02x nend %d\n",
         ifd->bInterfaceNumber, ifd->bAlternateSetting,
         ifd->bInterfaceClass, ifd->bInterfaceSubClass,
         ifd->bNumEndpoints);

    /* class-specific descriptors under the interface: FORMAT_TYPE */
    {
        int found = 0;
        for (k = 0; ; k++) {
            struct usbd_desc_node *cn;
            usbd_descriptors_t *cu = desc_at(d, ni, 0, k, &cn);
            uint8_t *raw;
            if (cu == NULL)
                break;
            raw = usbd_raw_descriptor(cn);
            /* CS_AS_INTERFACE (0x24), FORMAT_TYPE (0x02) */
            if (raw[0] >= 11 && raw[1] == 0x24 && raw[2] == 0x02) {
                g_chans = raw[4] ? raw[4] : 1;
                g_bits  = raw[6];
                g_rate  = raw[8] | (raw[9] << 8) | (raw[10] << 16);
                found = 1;
                VLOG("  format: %d ch, %d bits, %d Hz\n",
                     g_chans, g_bits, g_rate);
            }
        }
        if (!found) {
            /* C270 rate-per-alt table (from io-snd's own enumeration) */
            static const int rate_by_alt[] = { 0, 16000, 24000, 32000, 48000 };
            if (g_alt < 5)
                g_rate = rate_by_alt[g_alt];
            VLOG("  (no FORMAT_TYPE descriptor; rate by alt: %d Hz)\n",
                 g_rate);
        }
    }

    /* endpoints under this interface: want isochronous IN; the leading
     * control-type entry (ep 0x00) is the default control pipe, which we
     * open for UAC1 class requests (SET_CUR sample rate). */
    for (k = 0; ; k++) {
        usbd_descriptors_t *eu = desc_at(d, ni, USB_DESC_ENDPOINT, k, &ne);
        usbd_endpoint_descriptor_t *ed;
        if (eu == NULL)
            break;
        ed = &eu->endpoint;
        VLOG("  ep %02x attr %02x maxpkt %d intv %d\n",
             ed->bEndpointAddress, ed->bmAttributes,
             ed->wMaxPacketSize, ed->bInterval);
        if ((ed->bmAttributes & 0x03) == 0x00 && ed->bEndpointAddress == 0) {
            if (g_ctl == NULL && usbd_open_pipe(d, eu, &g_ctl) == EOK)
                VLOG("  opened EP0 control pipe\n");
            continue;
        }
        if ((ed->bmAttributes & 0x03) == 0x01 &&
            (ed->bEndpointAddress & 0x80)) {
            uint8_t *raw = usbd_raw_descriptor(ne);
            if (raw[0] >= 9)
                VLOG("  audio ep: refresh %d synch %02x\n",
                     raw[7], raw[8]);
            g_payload = ed->wMaxPacketSize & 0x7ff;
            g_ep_addr = ed->bEndpointAddress;
            if (usbd_open_pipe(d, eu, &g_pipe) == EOK) {
                VLOG("  opened iso IN pipe (payload %d)\n", g_payload);
                return 0;
            }
            logf_("micd: usbd_open_pipe failed: %s\n", strerror(errno));
            return -1;
        }
    }

    logf_("micd: AS iface %d alt %d has no iso IN endpoint\n",
          iface, g_alt);
    return -1;
}

/* ---- URB plumbing ---------------------------------------------------- */

static void submit_plain(int id)
{
    int32_t fnum = 0, flen = 0;
    uint32_t flags = URB_DIR_IN;

    if (g_frame_off > 0) {
        if (usbd_get_frame(g_dev, &fnum, &flen) != EOK)
            VLOG("  usbd_get_frame failed\n");
        fnum += g_frame_off;
    } else {
        flags |= URB_ISOCH_ASAP;
    }
    if (usbd_setup_isochronous(g_urbs[id], flags, fnum,
            g_bufs[id], g_payload) != EOK)
        logf_("micd: plain iso setup failed\n");
    if (usbd_io(g_urbs[id], g_pipe, completion, NULL,
                USBD_TIME_INFINITY) != EOK)
        logf_("micd: plain iso submit failed: %s\n", strerror(errno));
}

static void completion(struct usbd_urb *urb, struct usbd_pipe *pipe,
                       void *handle)
{
    int id, i;
    uint32_t st, len;
    double el;

    for (id = 0; id < g_n_urbs; id++)
        if (g_urbs[id] == urb)
            break;
    if (id == g_n_urbs)
        return;

    usbd_urb_status(urb, &st, &len);

    if (g_mode == 1) {             /* plain isoch: one packet per URB */
        if ((st & USBD_URB_STATUS_MASK) == USBD_STATUS_CMP && len > 0) {
            fwrite(g_bufs[id], 1, len, g_out);
            g_bytes += len;
            g_frames_ok++;
        } else {
            g_frames_err++;
        }
        el = now_elapsed();
        if (g_secs > 0 && el >= g_secs) {
            g_done = 1;
            return;
        }
        submit_plain(id);
        return;
    }
    if (len == 0)
        g_stalled++;             /* URB completed with nothing in it  */
    else
        g_stalled = 0;
    static int giveup = -1;
    if (giveup < 0) {          /* MICD_GIVEUP=0 disables the bail  */
        const char *e = getenv("MICD_GIVEUP");
        giveup = e ? atoi(e) : 100;
    }
    if (giveup > 0 && g_stalled > giveup) {
        logf_("micd: %d stalled URBs, giving up (urb status %08x)\n",
              (int)g_stalled, st);
        g_done = 1;
        return;
    }

    for (i = 0; i < g_n_frames; i++) {
        usbd_isoch_frame_request_t *fr = &g_flist[id][i];
        if (fr->frame_len > 0 && fr->frame_status == EOK) {
            fwrite(g_bufs[id] + i * g_payload, 1, fr->frame_len, g_out);
            g_bytes += fr->frame_len;
            g_frames_ok++;
        } else {
            g_frames_err++;
        }
        if (g_verbose && g_frames_ok + g_frames_err <= g_n_frames)
            logf_("  frame[%d] status %08x len %d\n",
                  i, fr->frame_status, fr->frame_len);
    }

    el = now_elapsed();
    if (g_secs > 0 && el >= g_secs) {
        g_done = 1;
        return;                         /* let the pipe drain, no resubmit */
    }

    for (i = 0; i < g_n_frames; i++) {
        g_flist[id][i].frame_status = 0;
        g_flist[id][i].frame_len    = g_payload;
    }
    if (g_resetup) {
        /* devu-uvc re-runs the isoch setup before every resubmit */
        int32_t sframe = 0;
        uint32_t sflags = URB_DIR_IN | URB_ISOCH_ASAP;
        if (g_sframe_off > 0) {
            int32_t cfrm = 0, cfln = 0;
            usbd_get_frame(g_dev, &cfrm, &cfln);
            sframe = cfrm + g_sframe_off;
            sflags = URB_DIR_IN;
        }
        if (usbd_setup_isochronous_stream(urb,
                sflags, sframe,
                g_bufs[id], g_n_frames * g_payload,
                g_flist[id], g_n_frames) != EOK)
            logf_("micd: isoch re-setup failed\n");
    }
    if (usbd_io(urb, pipe, completion, handle, USBD_TIME_INFINITY) != EOK)
        logf_("micd: resubmit failed: %s\n", strerror(errno));
}

/* Send the UAC1 SET_CUR sampling-frequency request.  Linux's snd-usb-audio
 * always issues this before streaming; some firmwares (incl. the C270's)
 * don't transmit until it lands.  Try the endpoint recipient first
 * (UAC1 4.6.1.2), then the interface recipient. */
static int set_cur_rate(void)
{
    struct usbd_urb *urb;
    uint8_t *buf;
    int rc = -1;

    if (g_ctl == NULL) {
        logf_("micd: no control pipe for SET_CUR\n");
        return -1;
    }
    urb = usbd_alloc_urb(NULL);
    buf  = usbd_alloc(3);
    if (urb == NULL || buf == NULL)
        goto out;
    buf[0] = g_rate & 0xff;
    buf[1] = (g_rate >> 8) & 0xff;
    buf[2] = (g_rate >> 16) & 0xff;

    {
        uint32_t st, len;
        int recipient;
        for (recipient = 0; recipient < 2; recipient++) {
            uint16_t rtype = recipient == 0
                ? USB_TYPE_CLASS | USB_RECIPIENT_ENDPOINT   /* 0x22 */
                : USB_TYPE_CLASS | USB_RECIPIENT_INTERFACE; /* 0x21 */
            uint16_t index = recipient == 0
                ? (uint16_t)((g_as_iface << 8) | g_ep_addr)
                : (uint16_t)(g_as_iface << 8);
            if (usbd_setup_vendor(urb, URB_DIR_OUT, 0x01 /* SET_CUR */,
                    rtype, 0x01 << 8 /* SAM_FREQ_CONTROL */, index,
                    buf, 3) != EOK)
                continue;
            if (usbd_io(urb, g_ctl, NULL, NULL, 5000) != EOK)
                continue;
            usbd_urb_status(urb, &st, &len);
            logf_("micd: SET_CUR rate %d Hz (rtype %02x) -> urb %08x\n",
                  g_rate, rtype, st);
            if ((st & USBD_URB_STATUS_MASK) == USBD_STATUS_CMP) {
                rc = 0;
                if (recipient == 0)
                    continue;   /* also send the interface-recipient form;
                                 * some firmwares ACK one but act on the
                                 * other */
                break;
            }
        }
    }
out:
    if (buf)  usbd_free(buf);
    if (urb) usbd_free_urb(urb);
    return rc;
}

/* Find the FEATURE_UNIT on the AudioControl interface and unmute it.
 * UAC1 firmware can default the mic to muted, in which case the AS
 * endpoint transmits nothing no matter what alt setting is selected. */
static int unmute_feature_unit(void)
{
    struct usbd_desc_node *ni;
    usbd_interface_descriptor_t *ifd;
    uint8_t unit_id = 0;
    int k, rc = -1;

    if (g_dev_ac == NULL) {
        VLOG("  (no AC handle; skipping unmute)\n");
        return -1;
    }
    ifd = usbd_interface_descriptor(g_dev_ac, 1, 2, 0, &ni);
    if (ifd == NULL) {
        VLOG("  (no AC iface 2 descriptor)\n");
        return -1;
    }
    for (k = 0; ; k++) {
        struct usbd_desc_node *cn;
        usbd_descriptors_t *cu = desc_at(g_dev_ac, ni, 0, k, &cn);
        uint8_t *raw;
        if (cu == NULL)
            break;
        raw = usbd_raw_descriptor(cn);
        if (raw[0] >= 7 && raw[1] == 0x24 && raw[2] == 0x06) { /* FEATURE_UNIT */
            unit_id = raw[3];
            VLOG("  feature unit id %d\n", unit_id);
            break;
        }
    }
    if (unit_id == 0) {
        VLOG("  (no feature unit found)\n");
        return -1;
    }

    {
        struct usbd_urb *urb = usbd_alloc_urb(NULL);
        uint8_t *buf = usbd_alloc(1);
        uint32_t st, len;
        if (urb == NULL || buf == NULL)
            goto out;
        buf[0] = 0;             /* unmute */
        if (usbd_setup_vendor(urb, URB_DIR_OUT, 0x01 /* SET_CUR */,
                USB_TYPE_CLASS | USB_RECIPIENT_INTERFACE, /* 0x21 */
                0x01 << 8 /* MUTE_CONTROL, channel 0 */,
                (unit_id << 8) | 2 /* (entity << 8) | AC iface */,
                buf, 1) != EOK)
            goto out;
        if (usbd_io(urb, g_ctl, NULL, NULL, 5000) != EOK)
            goto out;
        usbd_urb_status(urb, &st, &len);
        logf_("micd: SET_CUR unmute (unit %d) -> urb %08x\n",
              unit_id, st);
        if ((st & USBD_URB_STATUS_MASK) == USBD_STATUS_CMP)
            rc = 0;
out:
        if (buf)  usbd_free(buf);
        if (urb) usbd_free_urb(urb);
    }
    return rc;
}

/* ---- insertion / removal ---------------------------------------------- */

static void insertion(struct usbd_connection *c, usbd_device_instance_t *ins)
{
    logf_("micd: insertion vid=%04x did=%04x class=%02x.%02x.%02x "
          "cfg=%d iface=%d alt=%d devno=%d\n",
          ins->ident.vendor, ins->ident.device, ins->ident.dclass,
          ins->ident.subclass, ins->ident.protocol,
          ins->config, ins->iface, ins->alternate, ins->devno);

    if (ins->ident.vendor != (uint32_t)g_vid ||
        ins->ident.device != (uint32_t)g_did) {
        VLOG("  (not our device, ignoring)\n");
        return;
    }
    g_insert_seen = 1;

    if (g_cammode) {
        /* camera experiment: claim the video streaming interface (0e.02)
         * and stream its iso IN endpoint with the same URB code */
        if (ins->ident.dclass != 0x0e || ins->ident.subclass != 0x02) {
            VLOG("  (not the video streaming interface, ignoring)\n");
            return;
        }
    } else {
    /* Only claim audio interfaces (class 01).  The video interfaces
     * (0e.*) stay free for the sensor framework's camera driver. */
    if (ins->ident.dclass != USB_CLASS_AUDIO) {
        VLOG("  (not an audio interface, ignoring)\n");
        return;
    }
    if (ins->ident.subclass == USB_SUBCLASS_AUDIOCTL) {
        /* hold the AudioControl interface like io-snd does; some devices
         * gate streaming on the function being fully claimed */
        if (g_dev_ac == NULL) {
            if (usbd_attach(c, ins, 0, &g_dev_ac) == EOK && g_devreset) {
                logf_("micd: port-resetting device (-r)\n");
                usbd_reset_device(g_dev_ac);
            }
        }
        return;
    }
    if (ins->ident.subclass != USB_SUBCLASS_AUDIOSTR) {
        VLOG("  (not the AudioStreaming interface, ignoring)\n");
        return;
    }
    }
    if (g_stream_started) {
        VLOG("  (stream already started, ignoring)\n");
        return;
    }

    g_as_iface = ins->iface;

    if (usbd_attach(c, ins, 0, &g_dev) != EOK) {
        logf_("micd: usbd_attach(AS iface %d) failed\n", g_as_iface);
        g_failed = 1;
        return;
    }

    /* Selecting the alternate setting fixes the sample rate on UAC1 and
     * brings the iso endpoint into existence.  This MUST happen before
     * usbd_open_pipe(): at alt 0 the endpoint has no XHCI ring, and a
     * pipe opened too early fails every transfer with "out of TRBs
     * (enq_idx = -1)". */
    if (usbd_select_interface(g_dev, g_as_iface, g_alt) != EOK) {
        logf_("micd: usbd_select_interface(iface %d alt %d): %s\n",
              g_as_iface, g_alt, strerror(errno));
        g_failed = 1;
        return;
    }
    VLOG("  alt %d selected on iface %d\n", g_alt, g_as_iface);

    if (find_audio_stream(g_dev, ins->config, g_as_iface) != 0) {
        g_failed = 1;
        return;
    }

    /* URBs, buffers, frame lists */
    {
        int i, k;
        for (i = 0; i < g_n_urbs; i++) {
            if (g_mode == 0) {
                if (usbd_alloc_isochronous_frame_list(g_n_frames,
                        &g_flist[i]) != EOK)
                    goto oom;
                for (k = 0; k < g_n_frames; k++) {
                    g_flist[i][k].frame_status = 0;
                    g_flist[i][k].frame_len    = g_payload;
                }
                g_bufs[i] = usbd_alloc(g_n_frames * g_payload);
            } else {
                g_bufs[i] = usbd_alloc(g_payload);
            }
            g_urbs[i] = usbd_alloc_urb(NULL);
            if (g_urbs[i] == NULL || g_bufs[i] == NULL)
                goto oom;
        }
    }

    if (!g_cammode) {
    /* UAC1 bring-up sequence: unmute the mic, then set the sample
     * rate, before streaming. */
    unmute_feature_unit();
    set_cur_rate();
    }

    g_stream_started = 1;
    clock_gettime(CLOCK_MONOTONIC, &g_t0);
    logf_("micd: streaming %d Hz %d-bit %d-ch from iface %d alt %d "
          "(payload %d, %d urbs x %d frames)\n",
          g_rate, g_bits, g_chans, g_as_iface, g_alt,
          g_payload, g_n_urbs, g_n_frames);

    {
        int i, rc;
        for (i = 0; i < g_n_urbs; i++) {
            if (g_mode == 1) {
                submit_plain(i);
                continue;
            }
            int rc;
            {
                int32_t sframe = 0;
                uint32_t sflags = URB_DIR_IN | URB_ISOCH_ASAP;
                if (g_sframe_off > 0) {
                    int32_t cfrm = 0, cfln = 0;
                    usbd_get_frame(g_dev, &cfrm, &cfln);
                    sframe = cfrm + g_sframe_off;
                    sflags = URB_DIR_IN;
                }
                rc = usbd_setup_isochronous_stream(g_urbs[i],
                        sflags, sframe,
                        g_bufs[i], g_n_frames * g_payload,
                        g_flist[i], g_n_frames);
            }
            if (rc != EOK) {
                logf_("micd: isoch setup failed\n");
                g_failed = 1;
                return;
            }
            if (usbd_io(g_urbs[i], g_pipe, completion, NULL,
                        USBD_TIME_INFINITY) != EOK) {
                logf_("micd: usbd_io submit failed: %s\n",
                      strerror(errno));
                g_failed = 1;
                return;
            }
        }
    }
    return;

oom:
    logf_("micd: out of memory allocating URBs\n");
    g_failed = 1;
}

static void removal(struct usbd_connection *c, usbd_device_instance_t *ins)
{
    logf_("micd: removal (iface %d)\n", ins->iface);
    g_done = 1;
}

/* ---- WAV header ------------------------------------------------------- */

static void put32(FILE *f, uint32_t v) { fwrite(&v, 4, 1, f); }
static void put16(FILE *f, uint16_t v) { fwrite(&v, 2, 1, f); }

static void wav_header(FILE *f, uint32_t data_len)
{
    uint32_t byte_rate = g_rate * g_chans * g_bits / 8;
    rewind(f);
    fwrite("RIFF", 1, 4, f);  put32(f, 36 + data_len);
    fwrite("WAVE", 1, 4, f);
    fwrite("fmt ", 1, 4, f);  put32(f, 16);
    put16(f, 1);               put16(f, g_chans);
    put32(f, g_rate);          put32(f, byte_rate);
    put16(f, g_chans * g_bits / 8);
    put16(f, g_bits);
    fwrite("data", 1, 4, f);  put32(f, data_len);
}

/* ---- main ------------------------------------------------------------- */

static double now_elapsed(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (ts.tv_sec - g_t0.tv_sec) + (ts.tv_nsec - g_t0.tv_nsec) / 1e9;
}

int main(int argc, char **argv)
{
    usbd_device_ident_t ident = {
        USBD_CONNECT_WILDCARD, USBD_CONNECT_WILDCARD,
        USBD_CONNECT_WILDCARD, USBD_CONNECT_WILDCARD,
        USBD_CONNECT_WILDCARD
    };
    usbd_funcs_t funcs = { _USBDI_NFUNCS, insertion, removal, NULL };
    usbd_connect_parm_t parm;
    const char *path = NULL;
    int c, t, wait_secs, rc;

    while ((c = getopt(argc, argv, "vecf:F:a:t:o:p:n:u:m:R:")) != -1) {
        switch (c) {
        case 'a': g_alt = strtol(optarg, NULL, 0); break;
        case 't': g_secs = atoi(optarg); break;
        case 'o': g_outpath = optarg; break;
        case 'p': path = optarg; break;
        case 'n': g_n_frames = atoi(optarg); break;
        case 'u': g_n_urbs = atoi(optarg); break;
        case 'm': g_mode = atoi(optarg); break;
        case 'R': g_resetup = atoi(optarg); break;
        case 'e': g_devreset = 1; break;
        case 'c': g_cammode = 1; g_alt = 11; break;
        case 'f': g_frame_off = atoi(optarg); break;
        case 'F': g_sframe_off = atoi(optarg); break;
        case 'v': g_verbose++; break;
        default: goto usage;
        }
    }
    if (optind < argc)      g_vid = strtol(argv[optind++], NULL, 16);
    if (optind < argc)      g_did = strtol(argv[optind++], NULL, 16);
    g_alt &= 0xff;
    if (g_n_frames < 1)     g_n_frames = 1;
    if (g_n_urbs < 1)       g_n_urbs = 1;
    if (g_n_urbs > MAX_URBS) g_n_urbs = MAX_URBS;

    g_out = fopen(g_outpath, "w");
    if (g_out == NULL) {
        perror(g_outpath);
        return 1;
    }
    wav_header(g_out, 0);           /* placeholder, fixed up at the end */

    ident.vendor = g_vid;
    ident.device = g_did;

    memset(&parm, 0, sizeof(parm));
    parm.path         = path;
    parm.vusb         = USB_VERSION;
    parm.vusbd        = USBD_VERSION;
    parm.flags        = 0;
    parm.evtbufsz     = 0;
    parm.ident        = &ident;
    parm.funcs        = &funcs;
    parm.connect_wait = USBD_CONNECT_WAIT;
    parm.evtprio      = 0;

    rc = usbd_connect(&parm, &g_conn);
    if (rc != EOK && path == NULL) {
        logf_("micd: connect on default path failed, retrying "
              "/dev/usb/io-usb-otg\n");
        parm.path = "/dev/usb/io-usb-otg";
        rc = usbd_connect(&parm, &g_conn);
    }
    if (rc != EOK || g_conn == NULL) {
        logf_("micd: usbd_connect failed\n");
        return 1;
    }
    logf_("micd: connected to USB stack, waiting for %04x:%04x...\n",
          g_vid, g_did);

    /* wait for stream to start and finish */
    wait_secs = (g_secs > 0 ? g_secs : 3600) + 30;
    {
        long last = -1;
        int last_log_s = -1;
        for (t = 0; t < wait_secs * 20 && !g_done && !g_failed; t++) {
            int el_s;
            usleep(50000);
            el_s = (int)now_elapsed();
            if (g_stream_started && el_s != last_log_s) {
                last_log_s = el_s;
                if (last >= 0)
                    logf_("micd: t=%ds bytes=%ld (+%ld) ok=%d err=%d\n",
                          el_s, g_bytes, g_bytes - last,
                          g_frames_ok, g_frames_err);
                last = g_bytes;
            }
        }
    }

    if (g_stream_started && !g_done)
        logf_("micd: wait timeout\n");

    if (g_pipe) {
        usbd_abort_pipe(g_pipe);
        usleep(100000);
        usbd_close_pipe(g_pipe);
    }
    if (g_dev) {
        usbd_select_interface(g_dev, g_as_iface, 0);   /* back to idle */
        usbd_detach(g_dev);
    }
    if (g_conn)
        usbd_disconnect(g_conn);

    wav_header(g_out, (uint32_t)g_bytes);
    fclose(g_out);

    {
        double el = g_stream_started ? now_elapsed() : 0.0;
        logf_("micd: %ld bytes, %d ok frames, %d err frames, "
              "%.2f s, effective rate %.0f Hz\n",
              g_bytes, g_frames_ok, g_frames_err, el,
              el > 0 ? (g_bytes / (g_bits / 8.0)) / el : 0.0);
    }
    return (g_bytes > 0) ? 0 : 1;

usage:
    fprintf(stderr,
        "usage: micd [-a alt] [-t secs] [-o out.wav] [-p usb-path] [-v] "
        "[vid did]\n");
    return 1;
}
