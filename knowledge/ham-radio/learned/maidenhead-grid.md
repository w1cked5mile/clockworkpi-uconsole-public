# Maidenhead grid locators

The only location format this repo records ([`../../../CLAUDE.md`](../../../CLAUDE.md)
§Conventions). Written 2026-09-24 for the learning platform (gap B9). Reference: ARRL "Grid
squares", linked in [`../README.md`](../README.md).

## Structure

A locator is built in pairs, each pair narrowing the previous one. Longitude always comes first.

| Pair | Characters | Divides into | Each cell is | Size near 35° N |
|---|---|---|---|---|
| Field | 2 letters, A–R | 18 × 18 | 20° longitude × 10° latitude | about 1,800 × 1,100 km |
| Square | 2 digits, 0–9 | 10 × 10 | 2° × 1° | about 180 × 110 km |
| Subsquare | 2 letters, a–x | 24 × 24 | 5′ × 2.5′ | about 7.6 × 4.6 km |

East–west sizes shrink toward the poles because meridians converge; the table's figures are for
this build's latitude band.

## Converting a position

Shift so everything is positive — add 180 to longitude and 90 to latitude — then take each pair
in turn. A worked example for a round-number position, 41.7° N 72.7° W (central Connecticut):

| Step | Longitude | Latitude |
|---|---|---|
| Shift | −72.7 + 180 = 107.3 | 41.7 + 90 = 131.7 |
| Field: divide by 20 and 10, take the whole part, 0 → A | 107.3 / 20 = 5 → **F** | 131.7 / 10 = 13 → **N** |
| Square: remainder, divide by 2 and 1 | 7.3 / 2 = 3 → **3** | 1.7 / 1 = 1 → **1** |
| Result | | **FN31** |

The subsquare repeats the process on what remains (× 12 for longitude, × 24 for latitude, 0 → a).
It needs more precision than a round-number position carries — ARRL headquarters (W1AW) nearby
publishes itself as FN31pr.

webdash computes the 6-character locator server-side (`gps.grid`) and in the browser with the
same algorithm.

## How precise is too precise

| Length | Area | Share it? |
|---|---|---|
| 4 characters | about 180 × 110 km | yes — a region |
| 6 characters | about 7.6 × 4.6 km | yes — a town |
| 8 characters | about 760 × 460 m | no — a neighbourhood, close to an address |

This repo uses 4 or 6 characters (EM95 is this build's square). Findings, captures, notes and
lab evidence never record more.
