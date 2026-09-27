# Operations runbook

- Status: Current (v0.1.0)
- Service owner: @rokogan
- Escalation contact: @rokogan
- Last rehearsed: 2026-09-27 (exe first run, tray menu, and Quit on the owner's PC)

## Service summary

- User journey served: TV brightness follows PotPlayer playback.
- Environment: each user's Windows PC and LG TV on their home network. No servers.
- Deployment unit: `PotPlayer-TV-Brightness.exe` from a GitHub release, or this repository run from source with `.venv\Scripts\pythonw.exe run.pyw`.
- External dependency: the TV's SSAP API on port 3001, and SSDP on the LAN to find it.
- Logs: `potplayer-tv-brightness.log` in `%APPDATA%\PotPlayer TV Brightness` (exe) or the repository folder (source). Status: tray icon tooltip.
- Version: the release the exe came from, or `git log -1` from source.

## Health check

1. Hover the tray icon: the tooltip shows the status (Idle, Watching, TV unreachable, HDR, or Restore waiting).
2. **Connect TV…** in the tray menu shows whether the TV is found and answers. From source, `uv run python -m scripts.tv_check` does the same.
3. Read the end of the log for errors.

## Start, stop, restart

- Start: the exe, or `.venv\Scripts\pythonw.exe run.pyw` from source. **Start with Windows** in the tray menu starts it at sign-in.
- Stop: tray icon, then **Quit**. It restores the TV first (up to about 15 s if the TV is slow).
- If the process is killed instead, nothing is lost: the original brightness stays in `restore.json` and is restored on the next start.

## Release the exe

Releases are immutable (a repository setting): once published, the tag and files cannot change, and GitHub signs a record of them. A bad build is fixed with a new version.

1. Set the version in `pyproject.toml` (the exe's version info reads it) and move the changelog entries under it, then merge to `main`.
2. On a Windows PC, run all [testing](../testing.md) commands in a fresh clone of that commit, then build there with `packaging\build.cmd` (needs Visual Studio Build Tools with C++; it compiles PyInstaller's launcher from its hash-pinned source). `dist\` then holds `PotPlayer-TV-Brightness.exe`, `THIRD-PARTY-NOTICES.txt`, and `SHA256SUMS.txt`.
3. Check that exact exe: Windows Defender (`MpCmdRun.exe -Scan -ScanType 3 -File <exe>`), VirusTotal, and live check 5 in [testing](../testing.md), on this PC and in Windows Sandbox.
4. Tag the commit: `git tag -a vX.Y.Z -m "vX.Y.Z"`, then `git push origin vX.Y.Z`.
5. Create a draft release with the three files and notes taken from the changelog, including the checksums: `gh release create vX.Y.Z dist/PotPlayer-TV-Brightness.exe dist/THIRD-PARTY-NOTICES.txt dist/SHA256SUMS.txt --draft --title vX.Y.Z --notes-file <notes>`.
6. Publish it with `gh release edit vX.Y.Z --draft=false`, then check it: `gh release verify vX.Y.Z` and `gh release verify-asset vX.Y.Z dist/PotPlayer-TV-Brightness.exe`.

## Update and roll back

- Exe: Quit, replace the exe with the new release, and start it. To roll back, use the previous release's exe. Settings stay in `%APPDATA%`.
- Source: `git pull` and `uv sync --locked`, then Quit and start the app again. To roll back, `git checkout <previous commit>` and run `uv sync --locked`.

There is no data migration; `settings.json` and `restore.json` are plain JSON. Source and exe keep separate files, so moving between them means connecting once more.

## Common failure playbooks

| Symptom | Diagnose | Fix |
| --- | --- | --- |
| Connect window finds no TV | TV off, another network (VPN, guest Wi-Fi), or SSDP blocked | Type the IP address; see [Connect your TV](../user/README.md#connect-your-tv) |
| "TV unreachable, retrying" | Is the TV on? Did its address change? | **Connect TV…** (and reserve the TV's IP in the router) |
| Pairing prompt every time | Log shows pairing; key file missing or rejected | Accept the prompt; check that `tv-client-key.txt` is writable |
| "Restore waiting for picture mode" | TV is in a different picture mode than when the movie started | Switch back to that mode; or Quit, set the value with the remote, delete `restore.json`, and start again |
| Writes fail after a TV firmware update | The Connect window or `tv_check --set 20` reports that the firmware blocks it | See the follow-up in [ADR-0002](../architecture/decisions/0002-control-tv-brightness-over-webos-ssap.md) |
| No tray icon | Log says "Already running" | Another copy is running: look under the tray's **^** arrow, or in Task Manager |
