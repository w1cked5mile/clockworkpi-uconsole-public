# US amateur licensing path

Receiving needs no license. **Transmitting on amateur bands does** — and this build's only
transmitter (the SX1262) operates in license-free ISM spectrum, so a license adds capability
rather than legalizing anything currently in use.

## The three classes

| Class | Exam | Questions | Privileges |
|---|---|---|---|
| Technician | Element 2 | 35 (26 to pass) | All VHF/UHF above 30 MHz, limited HF (10 m SSB, CW segments) |
| General | Element 3 | 35 (26 to pass) | Most HF phone/data — the class that opens worldwide operation |
| Amateur Extra | Element 4 | 50 (37 to pass) | All amateur privileges |

No Morse code requirement exists at any class. Question pools are public and rotate on a
three-year cycle — study the **current** pool.

## Getting licensed

1. Study: ARRL manuals, hamstudy.org, or the free pools at ncvec.org.
2. Register for an FCC FRN at fcc.gov (needed before the exam).
3. Take the exam through a Volunteer Examiner Coordinator (ARRL VEC, W5YI, GLAARG). Sessions run
   in person and online; multiple elements can be attempted in one sitting.
4. Pay the FCC application fee; the call sign appears in ULS within days.
5. Licenses last 10 years and renew without re-examination.

Costs are modest: exam session fee plus the FCC fee, roughly $50 total at the time of writing —
verify current amounts.

## What Technician gives this build

Technician covers **2 m (144–148 MHz)** and **70 cm (420–450 MHz)** in full, which is where the
useful VHF/UHF activity is: repeaters, simplex, APRS, and amateur satellites. That matches what a
portable device with a modest antenna can practically work.

It does **not** give this hardware transmit capability — the RTL-SDR is receive-only. Transmitting
requires a separate radio; the license is what makes acquiring one useful.

## Receive-only participation, today

Nothing below requires a license:

- Monitoring local 2 m/70 cm repeaters
- Decoding APRS position/telemetry packets
- Receiving amateur satellite downlinks and the ISS
- Decoding FT8/WSPR and reporting spots to PSKReporter/WSPRnet

That is a complete workflow for this build as specified, and a way to learn the bands before
sitting the exam.

## Local resources

- ARRL club finder: http://www.arrl.org/find-a-club
- Exam session search: http://www.arrl.org/find-an-amateur-radio-license-exam-session
- Repeater directories: https://www.repeaterbook.com/

Band-edge detail: [`band-plans-and-privileges.md`](band-plans-and-privileges.md).
