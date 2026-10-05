# SDR stack — rtl-sdr tools and SDR++

## Packages

**Corrected 2026-09-18** — `sudo aiov2_ctl --add-apps` does **not** work on this image (the
`hackergadgets-*` packages it would install aren't published anywhere reachable from this repo's
apt sources; confirmed 2026-09-16, see
[`../docs/logs/known-issues.md`](../docs/logs/known-issues.md)). Install the pieces individually
from Debian's own repos instead — confirmed working 2026-09-18:

```bash
sudo apt install -y rtl-sdr        # rtl_test, rtl_fm, rtl_power, rtl_tcp
sudo apt install -y gqrx-sdr       # GUI waterfall/receiver
```

`sdrpp` (SDR++ v1.3.0) is also present on this build, but with **no apt/dpkg record of how it got
there** — confirmed 2026-09-18 (`dpkg -S /usr/bin/sdrpp` finds nothing). It is plain SDR++, not
confirmed to be the `sdrpp-brown` fork this file and `configs/sdrpp/README.md` previously assumed
— don't rely on that fork-specific detail until reinstalled from a known source. Not reproducible
from this doc as written; if it needs reinstalling, get it from
[AlexandreRouma/SDRPlusPlus](https://github.com/AlexandreRouma/SDRPlusPlus) upstream (or the
`sdrpp-brown` fork specifically, if that's what's wanted) and note here which one and how.

## Before anything works

1. Power the rail: `aiov2_ctl SDR on`
2. DVB-T driver blacklist — **confirmed already applied and working on this build, 2026-09-18**:
   `/etc/modprobe.d/blacklist-rtl-dvb.conf` matches the staged
   [`../configs/modprobe.d/blacklist-rtl-dvb.conf`](../configs/modprobe.d/blacklist-rtl-dvb.conf),
   `lsmod | grep -i rtl28` returns nothing, and `rtl_test -t`/`rtl_fm` open the device cleanly
   with no `usb_claim_interface` error. If setting this up fresh, the file's own header has the
   install/verify/rollback steps.
3. Confirm: `rtl_test -t` → `Found 1 device(s)`. **Correction**: this build's tuner reports as
   `Found Rafael Micro R820T tuner`, not `R860` — confirmed 2026-09-16/18, and not treated as a
   hardware discrepancy (same R82xx family/register set; this `librtlsdr` build's tuner-ID table
   just doesn't have a separate R860 entry). Device identifies itself as `HackerGadgets, AIO_V2
   Ext, SN: <serial>`.

## Calibration and health

```bash
rtl_test -t                    # device + tuner detection
rtl_test -s 2048000 -d 0       # sample-loss check at 2.048 MS/s (30 s is enough)
rtl_test -p                    # PPM offset — let it run 10+ min from warm
rtl_power -f 88M:108M:100k -i 10 -1 scan.csv   # quick spectrum sanity sweep
```

Record the PPM figure and the highest loss-free sample rate in `knowledge/sdr/configs/` — every
later capture depends on both. Not yet done on this build.

## Expected limits on this build

- USB 2.0 shared bus on CM4: 2.4 MS/s is often lossy, 2.048 MS/s is the practical ceiling.
- 8-bit ADC: strong local signals desensitize the receiver. Manual gain, not AGC.
- Bias tee outputs 5 V — see [`../docs/reference/antennas-and-rf-connectors.md`](../docs/reference/antennas-and-rf-connectors.md).
- **Single tuner, one process at a time.** `readsb` (see
  [`adsb-tar1090.md`](adsb-tar1090.md)) holds the RTL-SDR continuously for ADS-B tracking once
  installed; `rtl_fm`/`gqrx`/`sdrpp` will fail to open the device while it's running. Use
  [`../configs/sdr/sdr-swap.sh`](../configs/sdr/sdr-swap.sh) to toggle between ADS-B mode and
  general SDR use — this isn't just a software lock, a single-tuner SDR can only listen to one
  frequency at a time regardless, so there's no way to run both simultaneously on this hardware.

## Airband voice (118–137MHz AM) — CLI without a GUI

```bash
sdr-swap.sh free        # readsb has to release the tuner first, if it's running
rtl_fm -f 127.85M -M am -s 12k -g 40 - | aplay -r 12000 -f S16_LE -
```

**Gotcha (hit and fixed 2026-09-18):** `aplay -r` takes a plain integer sample rate, not
`rtl_fm`'s `k`/`M` suffix shorthand — `-r 12k` fails with `aplay: invalid rate argument '12k'`.
`aplay` exiting on that error closes the pipe under `rtl_fm`, which then prints its normal
clean-shutdown message (`Signal caught, exiting! / User cancel, exiting...`) for *any* terminating
signal — that message alone doesn't mean anything is wrong with the tuning or the RTL-SDR itself.
Use `-r 12000`.

Frequencies: local tower/ground/approach frequencies are on sites like liveatc.net or
airnav.com — airport-specific, not listed here.

## webdash broadcast/airband hunt & listen (receive-only)

Added 2026-10-01. The webdash SDR view can hunt for local signals and listen to them in the
browser, without a GUI or a terminal on the device — details in
[`../docs/reference/webdash-architecture.md`](../docs/reference/webdash-architecture.md)'s "SDR
broadcast/airband" section. It's the same CLI tools underneath (`rtl_power`, `rtl_fm`, plus
`ffmpeg`), driven by a small host bridge:

- **Hunt** — a one-shot `rtl_power` sweep of **FM broadcast (88–108 MHz)** or **VHF airband
  (118–137 MHz AM)**, parsed into a station list (frequency / signal / SNR).
- **Listen** — `rtl_fm` demodulates (wide FM / NBFM / AM), `ffmpeg` encodes MP3, and the webdash
  streams it to an `<audio>` element, so it plays over the tailnet. NOAA weather radio
  (162.400–162.550 MHz, NBFM) has a dedicated channel picker.

Like the CLI, it needs the tuner free: the bridge **stops `readsb` for the duration and restarts
it after** (the same idea as `sdr-swap.sh free`), and it requires the **SDR rail already on**. One
tuner means hunt and listen are mutually exclusive.

**Broadcast AM (530–1710 kHz) is deliberately absent** — it's below this front end's ~24 MHz floor
and needs an upconverter this build doesn't have (see
[`../knowledge/sdr/learned/rtl-sdr-limits.md`](../knowledge/sdr/learned/rtl-sdr-limits.md)). Airband
takes the "AM" slot instead.

## SDR++ / gqrx (GUI)

Config starting points, band presets (including airband), and the settings worth recording:
[`../configs/sdrpp/README.md`](../configs/sdrpp/README.md).
