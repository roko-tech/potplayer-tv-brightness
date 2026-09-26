# User guide

## Install

Needs Windows 10 or 11, Python 3.12, [uv](https://docs.astral.sh/uv/), and PotPlayer.

```shell
git clone https://github.com/roko-tech/potplayer-tv-brightness.git
cd potplayer-tv-brightness
uv sync
```

## Connect your TV

Do this once. The TV must be on, and on the same home network as the PC (not a guest network).

1. Find the TV's IP address. On the TV, open **Settings > General > Network** and select the connection in use: **Wired Connection (Ethernet)**, or **Wi-Fi Connection > Other Network Settings > Advanced Wi-Fi Settings**. Menu names vary by model year. Your router's list of connected devices shows it too.
2. From the app folder, run this with your TV's address:

   ```shell
   uv run python -m scripts.tv_check --host 192.168.1.50
   ```

3. The TV asks whether to allow the connection. Select **Accept** with the remote within 60 seconds.

When it works, it prints:

```text
Saved TV address 192.168.1.50 to settings.json.
Picture mode: normal, OLED Pixel Brightness: 20
```

The address is saved in `settings.json` and the pairing key in `tv-client-key.txt`. The app uses both from then on.

- **Keep the address fixed.** Reserve the TV's IP in your router's DHCP settings, or it may change after a router restart.
- **Older TVs:** if the TV never shows the prompt, look for **LG Connect Apps** under **Settings > Network** and turn it on.
- **New address:** run the command again with the new address, then restart the app.
- **Pair again:** delete `tv-client-key.txt` and run the command again.

## Start

```shell
.venv\Scripts\pythonw.exe run.pyw
```

`pythonw` runs it without a console window. Starting it twice is harmless; the second copy exits. If no TV is connected yet, it says so and exits.

## Start with Windows

Create a Startup shortcut. Run this in PowerShell from the app folder:

```powershell
$app = (Get-Location).Path
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
| `settings.json` | `tv_host` (the TV's IP address, saved by `tv_check --host`) and `movie_brightness` (0 to 100, default 80) |
| `tv-client-key.txt` | TV pairing key. Treat it like a password; delete it to pair again. |
| `restore.json` | Original brightness still owed to the TV. Only exists while one is pending. |
| `potplayer-tv-brightness.log` | Activity and errors (256 KB, one backup) |

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `TV check failed: Cannot connect to wss://...` | The TV is off, the address is wrong, or the PC and TV are on different networks (guest Wi-Fi, VPN). Use just the address, like `192.168.1.50`, without `http://` or a port. |
| `Pairing refused: 403 Error: User rejected pairing` | **Decline** was selected on the TV. Run the command again and select **Accept**. |
| Times out while the prompt is showing | The prompt was not accepted within 60 seconds. Run the command again. |
| "No TV address in settings.json" when starting the app | [Connect your TV](#connect-your-tv) first. |
| Tooltip says "TV unreachable" | The TV is off or its address changed. Run `uv run python -m scripts.tv_check`; if the address changed, connect again with `--host` and restart the app. |
| Nothing happens when playing | Is PotPlayer minimized or paused? Check the log for errors. |
| Brightness stuck high after a movie | Hover the icon: a pending restore waits for the original picture mode. Switch back to it, or set the value yourself: `uv run python -m scripts.tv_check --set 20`, then delete `restore.json`. |
| Accept prompt shows up again | The TV forgot the key (e.g. after a factory reset). Accept it again. |

## Privacy

The app only talks to your TV on the local network. It sends nothing else anywhere and logs no keys.

## Known limitations

- Windows only. Tested with an LG C2 on webOS 25 and PotPlayer 64-bit. On another LG TV, `uv run python -m scripts.tv_check --set N` (N = its current value) shows quickly whether it accepts the brightness change.
- Brightness settings belong to the TV's current input. If you switch the TV to another input or app while a movie is still playing and the movie then ends, the restore writes to that input's picture mode (if the mode name matches).
- A picture mode change in the middle of a movie is not boosted until the next play.
