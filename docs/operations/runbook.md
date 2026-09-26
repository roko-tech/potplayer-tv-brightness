# Operations runbook

- Status: Current (v0.1.0)
- Service owner: @rokogan
- Escalation contact: @rokogan
- Last rehearsed: 2026-09-25 (start, crash, restart, and stop on the owner's PC)

## Service summary

- User journey served: TV brightness follows PotPlayer playback.
- Environment: the owner's Windows PC and LG C2 TV on the home network. No servers.
- Deployment unit: this repository folder, run from source with `.venv\Scripts\pythonw.exe run.pyw`.
- External dependency: the TV's SSAP API on port 3001.
- Logs: `potplayer-tv-brightness.log` in the app folder. Status: tray icon tooltip.
- Version: `git log -1` in the app folder.

## Health check

1. Hover the tray icon: the tooltip shows the status (Idle, Watching, TV unreachable, HDR, or Restore waiting).
2. `uv run python -m scripts.tv_check` confirms the TV is reachable and paired.
3. Read the end of the log for errors.

## Start, stop, restart

- Start: `.venv\Scripts\pythonw.exe run.pyw` from the app folder, or the Startup shortcut in the [user guide](../user/README.md).
- Stop: tray icon, then **Quit**. It restores the TV first (up to about 15 s if the TV is slow).
- If the process is killed instead, nothing is lost: the original brightness stays in `restore.json` and is restored on the next start.

## Update and roll back

```shell
git pull
uv sync --locked
```

Then Quit and start the app again. To roll back, `git checkout <previous commit>` and run `uv sync --locked`. There is no data migration; `settings.json` and `restore.json` are plain JSON.

## Common failure playbooks

| Symptom | Diagnose | Fix |
| --- | --- | --- |
| "No TV address in settings.json" at start | No TV connected yet, or `settings.json` is invalid (see the log) | [Connect your TV](../user/README.md#connect-your-tv) |
| "TV unreachable, retrying" | Is the TV on? `tv_check`; ping the IP | If the address changed, run `tv_check --host <new IP>` (and reserve the TV's IP in the router), then restart the app |
| Pairing prompt every time | Log shows pairing; key file missing or rejected | Accept the prompt; check that `tv-client-key.txt` is writable |
| "Restore waiting for picture mode" | TV is in a different picture mode than when the movie started | Switch back to that mode, or set the value with `tv_check --set N` and delete `restore.json` |
| Writes fail after a TV firmware update | `tv_check --set 20` returns an error | See the follow-up in [ADR-0002](../architecture/decisions/0002-control-tv-brightness-over-webos-ssap.md) |
| No tray icon | Log says "Already running" | Another copy is running; check Task Manager for `pythonw.exe` |
