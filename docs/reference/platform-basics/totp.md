# TOTP and the dashboard login

Written 2026-09-25 (gap P7). References: RFC 6238 and NIST SP 800-63B (linked in
[`../../../knowledge/README.md`](../../../knowledge/README.md) §Platform references). Code:
[`../../../webdash/app/auth.py`](../../../webdash/app/auth.py).

## How a six-digit code works

At setup, webdash creates a random **shared secret** and shows it once as a QR code; your
authenticator app stores it. Each side then computes the same code from the secret and the
current time, cut into 30-second steps (RFC 6238). Nothing is sent between them — the code
matches because both know the secret and both know the time.

webdash accepts the current step and one either side (`valid_window=1`), so the two clocks may
differ by at least 30 seconds (up to nearly 60, depending on where in the step the check falls).

## Why the clock matters here

Fancy has no RTC backup cell. After an offline cold boot the system clock can be far off, and
every code will be rejected until the clock is right — NTP when online, or GPS time if it is fed
to chrony (*unverified*). See
[`../../../knowledge/rf-fundamentals/learned/gnss-basics.md`](../../../knowledge/rf-fundamentals/learned/gnss-basics.md#gnss-time-the-rtc-and-ntp).

## Why "not recoverable"

The secret is stored only in `~/.config/uconsole-webdash/auth.json` and your authenticator. If
you lose the authenticator, there is no second copy to show you: the reset is to delete
`auth.json` and set the account up again ([`../../../software/webdash.md`](../../../software/webdash.md)).
Password plus TOTP is two factors: something you know and something you have.
