# ADR-0006: Pair unsigned and write through an alert when LG blacklists the signature

- Date: 2026-11-12
- Status: Accepted
- Owners: @rokogan
- Related: [ADR-0002](0002-control-tv-brightness-over-webos-ssap.md) (its follow-up), [references](../../references.md#lg-tv-integration)

## Context

On 2026-11-12, after a firmware update, the owner's LG C2 (OLED48C26LA) answered the app's registration with `403 Pairing rejected: blacklisted certificate detected`. The app could not connect, and the Connect window said the firmware blocks it. The same rejection of the signed manifest in `pairing.json` (LG's `com.lge.test` signature, as published in lgtv2) is reported on 2026 C5 and C6 firmware and in Home Assistant, aiowebostv, and ioBroker.

Measured on that TV, using the same client key, with the signature removed:

- registration succeeds, without a new Accept prompt;
- `ssap://settings/getSystemSettings` still reads the picture mode and brightness;
- `ssap://settings/setSystemSettings` fails with `401 insufficient permissions`;
- a notification alert whose `onclose` calls `luna://com.webos.settingsservice/setSystemSettings` changes the brightness once the alert is closed: 20 → 25 → 20, read back each time.

## Decision drivers

- Work again on TVs whose firmware blacklists the signature.
- No change for TVs that still accept it: that path is the one verified in ADR-0002.
- Still write only `backlight`, to the current picture mode, with no Developer Mode or rooting.

## Considered options

### Signed first, unsigned on a blacklisted signature (chosen)

Send the signed manifest as before. Only if the TV's error says `blacklisted`, send the registration again on the same socket without `signatures` and `signed`, asking for the union of both permission lists. aiowebostv shipped the same registration fallback on 2026-11-08. When unsigned, write the brightness through the alert method from ADR-0002, with bscpylgtv's payload.

### Always unsigned

One code path, but it would change the verified behavior on TVs that still accept the signature, and it is untested whether older firmware grants alerts to unsigned clients.

### Keep the signed manifest only

The app stays broken on updated TVs, including the owner's.

## Decision

- `tv.py` registers with `pairing.json`. On a registration error containing `blacklisted`, it retries once, unsigned, with the saved key. `Session.signed` records which one the TV took. Other errors, such as a declined prompt, are not retried.
- Reads are unchanged.
- `set_backlight` writes `ssap://settings/setSystemSettings` when signed. When unsigned, it creates an alert whose button, `onclose`, and `onfail` all run the luna `setSystemSettings` call with `{"category": "picture", "settings": {"backlight": N}}`, then closes it. Callers still clamp N to 0 to 100.

## Consequences

### Positive

- The app works again on the owner's TV, and existing pairings keep working without a new prompt.
- TVs that accept the signature behave as before.
- No new dependency.

### Negative and tradeoffs

- The TV does not report the luna call's result. If a firmware ignores it, the app believes the brightness changed; `tv_check --set N` reads it back and shows it.
- The alert method is undocumented, and LG could block it too. No method without Developer Mode or rooting is known after that.
- Each session on such a TV costs one extra registration round trip on the LAN.
- If the connection drops between creating and closing the alert, the alert may stay open, and closing it later would apply that value. The two requests are sent back to back.

### Follow-up

- If `tv_check --set N` stops reading back N on unsigned TVs, LG has blocked alert calls too. The Connect window's "firmware blocks" message and the known limitations then apply again.

## Validation

- Unit tests in `tests/test_tv.py`: an unsigned retry on a blacklisted signature on the same socket with the same key, the alert write and close, and no retry after any other refusal.
- Live, 2026-11-12, on the owner's C2 after the update: `tv_check` read `normal` at 20; `--set 25` and `--set 20` each read back within 0.5 s.
