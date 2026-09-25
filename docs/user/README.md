# User guide

## Start

```shell
cd D:\MyScripts\potplayer-tv-brightness
uv sync
.venv\Scripts\pythonw.exe run.pyw
```

`pythonw` runs it without a console window. Starting it twice is harmless; the second copy exits.

On first use the TV shows an Accept prompt. Accept it with the remote within 60 seconds. The key is saved in `tv-client-key.txt`.

## Start with Windows

Create a Startup shortcut (PowerShell):

```powershell
$app = "D:\MyScripts\potplayer-tv-brightness"
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\PotPlayer TV Brightness.lnk")
$shortcut.TargetPath = "$app\.venv\Scripts\pythonw.exe"
$shortcut.Arguments = "run.pyw"
$shortcut.WorkingDirectory = $app
$shortcut.Save()
```

Delete that `.lnk` file to stop auto-start.

## Choose the movie brightness

Right-click the tray icon, then **Movie brightness**, and pick 30 to 100. It applies right away if a movie is playing and is saved for next time. For another value, edit `movie_brightness` in `settings.json` and restart the app.

## What it does

- **Playing** means a PotPlayer window is playing and is not minimized. The app acts once that state has held for about a second, so skipping between playlist items does not flicker the screen.
- Each time playback starts, it reads the current brightness from the TV. That is the value it restores, so changes you make with the remote between movies are kept.
- It stores the original per picture mode and only writes it back to that same mode.
- **HDR and Dolby Vision** picture modes are left alone. HDR already runs at full brightness, and a lower movie value would dim it.
- If the restore can't happen yet (TV off, or the TV is in a different picture mode, for example still in HDR), it retries every 10 seconds. The pending value is kept in `restore.json`, so a crash or reboot still ends with the original brightness.

## Settings and files

All files live in the app folder and are not committed to Git.

| File | Purpose |
| --- | --- |
| `settings.json` | `tv_host` (TV IP address, default `192.168.8.145`) and `movie_brightness` (0 to 100, default 80) |
| `tv-client-key.txt` | TV pairing key. Treat it like a password; delete it to pair again. |
| `restore.json` | Original brightness still owed to the TV. Only exists while one is pending. |
| `potplayer-tv-brightness.log` | Activity and errors (256 KB, one backup) |

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Tooltip says "TV unreachable" | TV is off or the IP changed. Run `uv run python -m scripts.tv_check`; fix `tv_host`. |
| Nothing happens when playing | Is PotPlayer minimized or paused? Check the log for errors. |
| Brightness stuck high after a movie | Hover the icon: a pending restore waits for the original picture mode. Switch back to it, or set the value yourself: `uv run python -m scripts.tv_check --set 20`, then delete `restore.json`. |
| Accept prompt shows up again | The TV forgot the key (e.g. after a factory reset). Accept it again. |

## Privacy

The app only talks to your TV on the local network. It sends nothing else anywhere and logs no keys.

## Known limitations

- Windows only. Tested with an LG C2 on webOS 25 and PotPlayer 64-bit.
- Brightness settings belong to the TV's current input. If you switch the TV to another input or app while a movie is still playing and the movie then ends, the restore writes to that input's picture mode (if the mode name matches).
- A picture mode change in the middle of a movie is not boosted until the next play.
