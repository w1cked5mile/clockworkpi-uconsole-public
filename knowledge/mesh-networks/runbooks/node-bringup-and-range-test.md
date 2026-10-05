# Runbook — Meshtastic node bring-up and range test

Two parts: prove the node works, then measure what it actually reaches. The second part needs a
**second node** — a single node cannot demonstrate RF function.

## Part 1 — bring-up

### Preconditions

- [ ] **915 MHz antenna attached** (transmitting without one risks the SX1262 PA)
- [ ] `dtparam=spi=on` and `dtoverlay=spi1-1cs` applied, system rebooted
- [ ] `devterm-printer` masked if present ([`../../../configs/systemd/README.md`](../../../configs/systemd/README.md))

### Steps

```bash
aiov2_ctl LORA on
ls /dev/spidev1.*                 # spidev1.0 must exist
meshtastic --info                 # radio detected, region, firmware version
meshtastic --configure ../../../configs/meshtastic/us915.yaml
meshtastic --nodes                # own node listed; others if any are in range
```

- [ ] Radio detected, region **US**, preset LONG_FAST
- [ ] Firmware version recorded in [`../../../docs/logs/firmware-versions.md`](../../../docs/logs/firmware-versions.md)

## Part 2 — range test

### Setup

- [ ] Second node configured identically (region, preset, channel, PSK)
- [ ] Both antennas vertical, away from bodies and metal
- [ ] Fixed node's position and height recorded (general location only)
- [ ] GPS running on the mobile node for distance, or waypoints noted manually

### Method

1. Baseline at 10 m: send a message each way, confirm both directions.
2. Move in steps (250 m urban, 1 km open). At each stop:
   - send a message each way
   - record SNR and RSSI from `meshtastic --nodes`
   - note terrain, line of sight, and obstructions
3. Continue until two consecutive stops fail in both directions.
4. Repeat once on a different path if the first was terrain-limited.

### Record

| Distance | Line of sight | RSSI (dBm) | SNR (dB) | TX→ | ←RX | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |

## Interpretation

- **SNR near or below 0 dB with successful decodes** is normal for LoRa — processing gain is
  working as designed.
- Failures with strong RSSI point at configuration mismatch, not range.
- Compare measured range against the link-budget estimate in
  [`../learned/lora-modulation-and-airtime.md`](../learned/lora-modulation-and-airtime.md);
  a large gap usually means antenna height or obstruction, not power.

## Log it

Copy [`../../_templates/finding.md`](../../_templates/finding.md) into `../findings/` with the
table above, both nodes' settings, antennas, weather, and UTC time. Range results are only
comparable when the configuration is recorded alongside them.

## Legal

US 902–928 MHz operation under FCC Part 15 with the region setting applied. Do not override
channel, power, or dwell settings to extend range.
