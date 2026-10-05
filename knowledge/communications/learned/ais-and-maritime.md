# AIS and maritime signals

AIS is the maritime counterpart to ADS-B: vessels broadcast identity, position, course, and speed
in the clear, on fixed VHF channels.

## The signal

| Property | Value |
|---|---|
| Channel A | 161.975 MHz (AIS 1) |
| Channel B | 162.025 MHz (AIS 2) |
| Modulation | GMSK, 9600 bps, 25 kHz channels |
| Access | Self-organizing TDMA — vessels reserve time slots |
| Range | VHF line of sight — typically 20–60 km from a coastal receiver |

Both channels sit within a 50 kHz span, so a single capture at ≥100 kS/s covers them at once.

## Message content

| Type | Contents |
|---|---|
| 1/2/3 | Position report: MMSI, lat/lon, course, speed, heading, navigation status |
| 4 | Base-station report with UTC |
| 5 | Static/voyage data: vessel name, call sign, type, dimensions, destination, ETA |
| 18/19 | Class B position reports (smaller vessels) |
| 21 | Aids to navigation (buoys, lighthouses) |

MMSI is the vessel identifier; the first three digits encode the flag state.

## Receiving it

| Requirement | Detail |
|---|---|
| Antenna | Marine VHF band vertical, ~160 MHz — a ¼-wave is ~468 mm |
| Location | Coastal or navigable inland waterway; landlocked sites hear nothing |
| Software | `rtl_ais` (direct from RTL-SDR), `AIS-catcher`, or `gnuais` |
| Output | NMEA sentences, feedable to OpenCPN or an aggregator |

```bash
PPM=1                        # dongle frequency error, measured ≈ +1 ppm 2026-09-24 (checklist 3.6)
sudo systemctl stop readsb   # readsb holds the SDR; run `sudo systemctl start readsb` when done
# uses: rtl-ais (installed 2026-09-24 via apt)

rtl_ais -n -p "$PPM"        # decode both channels, print NMEA
```

**your location is inland.** Local AIS reception is not expected here — this is a travel/coastal
capability, and the note exists so a silent receiver is not mistaken for a fault.

## Legality

AIS is an unencrypted safety broadcast intended for public reception; receiving and displaying it
is routine, and aggregators (MarineTraffic, AISHub) run on volunteer receivers. Feeding one
publishes your receiver's location.

## Related maritime signals

| Signal | Frequency | Notes |
|---|---|---|
| Marine VHF voice | 156–162 MHz | Ch 16 (156.800) is the distress/calling channel — monitor, never transmit without authorization |
| NAVTEX | 518 kHz | HF — out of reach without an upconverter |
| EPIRB / SART | 406 MHz | Distress beacons; receive-only curiosity, never interfere |
