# Bundled static data

## `nwr-stations.json`

NOAA Weather Radio (NWR All Hazards) transmitter table — **1035 US transmitters**, each as
`{call, freq_hz, lat, lon, site, st, pw}` (callsign, channel in Hz, coordinates, site name, state,
power in watts). Used by the SDR view to auto-select the predicted-strongest local NWR channel from
the device's GPS fix (see `app/static/js/sdr.js`, `bestNwr`).

- **Source:** the National Weather Service NWR county-coverage dataset (`cclData`) backing
  <https://www.weather.gov/nwr/station_listing>, fetched **2026-10-03** from
  `https://www.weather.gov/source/nwr/JS/ccl-data.js`. The bulky per-county SAME arrays were dropped
  and coordinates rounded to 4 dp; frequencies converted MHz→Hz.
- **Static, no runtime egress.** This is a one-time authoring-time capture bundled into the image;
  the dashboard reads only this local file. Nothing in the app fetches NWR data at runtime.
- **Refresh:** re-run the fetch+parse (see `docs/logs/build-log.md`, 2026-10-03 NWR entry) to update.
  Transmitter sites change rarely; treat this as a point-in-time snapshot.
- **Selection ≠ nearest.** The picker ranks by `power / distance²` (a free-space received-power
  proxy), not raw distance — a closer low-power site can be weaker than a farther high-power one.
  Confirmed on-air at grid FM03: 162.400 (KEC95, Aynor SC, 1000 W, 40 km) beats 162.500 (WNG628,
  Georgetown SC, 300 W, 33 km), which measured at the noise floor.
