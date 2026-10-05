# Runbook — ADS-B reception with tar1090

From a powered SDR rail to aircraft on a map, with numbers that make later comparisons meaningful.

## Preconditions

- [ ] `aiov2_ctl SDR on`; `rtl_test -t` passes
- [ ] 1090 MHz antenna connected (¼-wave ≈ 69 mm with radials, or a collinear)
- [ ] Decoder installed — `tar1090` is only the **web map**; it needs `dump1090-fa` or `readsb`
      behind it ([`../../../software/adsb-tar1090.md`](../../../software/adsb-tar1090.md))
- [ ] No other process holding the dongle (SDR++ closed, CLI tools stopped)

## 1. Start the decoder

```bash
systemctl list-units --type=service | grep -Ei 'dump1090|readsb|tar1090'
sudo systemctl start <decoder>.service
journalctl -u <decoder> -f          # watch for device errors on startup
```

## 2. Confirm decoding before opening the map

```bash
# message rate from the decoder's own status/stats output
curl -s localhost/tar1090/data/aircraft.json | head -40
```

Messages but no positions → normal for the first minute (CPR needs an even/odd pair) or a weak
signal. Zero messages → antenna, gain, or device contention.

## 3. Open the map

`http://<host>/tar1090/` — path depends on the package's web root.

## 4. Tune gain

Gain interacts with the 8-bit dynamic range: too much overloads and *reduces* decode rate.

```bash
# for each gain, run 5 minutes and record message + position rate
for g in 30 36 40 44 49; do
  echo "gain $g"   # set via the decoder's config, restart, sample the stats
done
```

Keep the gain with the highest **position** rate, not the highest message count.

## 5. Record the session

| Metric | Value |
|---|---|
| Antenna type / height / location | |
| Gain | |
| Messages per second (steady state) | |
| Positions per second | |
| Aircraft seen in 15 min | |
| Maximum range (km) | |
| UTC start / end | |

Write it into `../findings/` using [`../../_templates/finding.md`](../../_templates/finding.md).
That table is the baseline every antenna change is measured against.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `usb_claim_interface error -6` | DVB driver claimed the device — apply the modprobe blacklist |
| Zero messages, device fine | Antenna not resonant at 1090 MHz, or coax/connector fault |
| Messages but no positions | Weak signal (partial frames) or too little time elapsed |
| Rate drops as gain rises | Front-end overload — reduce gain |
| Decoder dies at start | Another process holds the dongle |

## Notes

- 978 MHz UAT carries additional US general-aviation traffic; some decoders support it with
  different settings.
- Feeding an aggregator network is optional and publishes your receiver location — a deliberate
  choice, not a default.
