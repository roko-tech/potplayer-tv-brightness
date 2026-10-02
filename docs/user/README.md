# User guide

## Install

Download **PotPlayer-TV-Brightness.exe** from the [latest release](https://github.com/roko-tech/potplayer-tv-brightness/releases/latest) and put it anywhere, for example in Documents. There is nothing to install.

Windows may show "Windows protected your PC", because the app is not signed. Click **More info**, then **Run anyway**.

To check the download (optional), compare `Get-FileHash .\PotPlayer-TV-Brightness.exe` in PowerShell with the release's `SHA256SUMS.txt`. With the [GitHub CLI](https://cli.github.com/), `gh release verify-asset <tag> PotPlayer-TV-Brightness.exe --repo roko-tech/potplayer-tv-brightness` also checks GitHub's signed record of the release.

## Connect your TV

Start the exe. The TV must be on, and on the same home network as the PC (not a guest network). No Developer Mode, rooting, or LG account is needed: the app pairs the way LG's own phone remote app does.

1. The **Connect your LG TV** window searches for a few seconds and lists your TV, for example `[LG] webOS TV OLED48C26LA`.
2. Click **Connect**.
3. The TV asks whether to allow the connection. Select **Accept** with the remote within 60 seconds.

The window closes, a sun icon appears in the tray, and a notification says the app is on.

If your TV is not listed:

- Check that it is on and on the same network (no VPN or guest Wi-Fi), then click **Search again**.
- Or type its IP address. On the TV, open **Settings > General > Network**, then **Wired Connection (Ethernet)** or **Wi-Fi Connection > Other Network Settings > Advanced Wi-Fi Settings**. Menu names vary by model year. Your router's device list shows it too.
- Older TVs: if the TV never asks to allow the connection, turn on **LG Connect Apps** under **Settings > Network**.

Tip: reserve the TV's IP address in your router's DHCP settings so it never changes. If it does change, use **Connect TV…** in the tray menu.

## Tray menu

Right-click the sun icon:

- **Movie brightness**: pick 30 to 100. It applies right away if a movie is playing and is saved for next time.
- **Dark scene brightness**: Off (the default), or a higher value for dark scenes. Only values above the movie brightness can be picked. See [Dark scenes](#dark-scenes).
- **Connect TV…**: opens the Connect window again.
- **Start with Windows**: starts the app when you sign in. If you move the exe, turn this off and on again.
- **Quit**: puts the original brightness back and exits.

Hover the icon to see the status; it is amber while the movie brightness is on. Windows may hide new tray icons under the **^** arrow; drag the sun onto the taskbar to keep it in view.

## What it does

- **Playing** means a PotPlayer window is playing and is not minimized. The app acts once that state has held for about a second, so skipping between playlist items does not flicker the screen.
- Each time playback starts, it reads the current brightness from the TV. That is the value it restores, so changes you make with the remote between movies are kept.
- It stores the original per picture mode and only writes it back to that same mode.
- **HDR and Dolby Vision** picture modes are left alone. HDR already runs at full brightness, and a lower movie value would dim it.
- If the restore can't happen yet (TV off, or the TV is in a different picture mode, for example still in HDR), it retries every 10 seconds. The pending value is kept in `restore.json`, so a crash or reboot still ends with the original brightness.

## Dark scenes

With **Dark scene brightness** on, the app also checks how bright the picture is, twice a second, while PotPlayer plays:

- When a scene stays dark for about 2 seconds, the TV goes up to the dark scene brightness. Once the picture has been bright again for about a second, it goes back to the movie brightness. So the change comes a moment after the scene changes, and the TV switches in one step, not a fade.
- Fades to black, short flashes, and scenes that are neither dark nor bright don't switch it, so it doesn't flicker.
- It looks at the whole PotPlayer window and goes by its brighter part: a scene is dark only when nearly all of the picture is dark. So a dark character or object in front of a bright background doesn't count, while a dark scene with a small lamp, subtitles, or black bars still does. If another window covers the center of PotPlayer, it doesn't measure.
- Each time playback starts, it starts at the movie brightness. Pause, minimize, and close still put your original brightness back, and HDR is still left alone.
- The log shows the measured level at each switch, for example `Picture level 45: dark`. The level is how bright the picture is when you leave out its brightest tenth, on a scale of 0 to 255. A scene counts as dark below 70 and as bright again above 100.

## Files

The exe keeps its files in `%APPDATA%\PotPlayer TV Brightness` (paste that into File Explorer's address bar). Run from source, they are in the repository folder instead.

| File | Purpose |
| --- | --- |
| `settings.json` | `tv_host` (the TV's IP address), `movie_brightness` (0 to 100, default 80), and `dark_scene_brightness` (0 is Off, the default; used only when above `movie_brightness`) |
| `tv-client-key.txt` | TV pairing key. Treat it like a password; delete it to pair again. |
| `restore.json` | Original brightness still owed to the TV. Only exists while one is pending. |
| `potplayer-tv-brightness.log` | Activity and errors (256 KB, one backup) |

## Update and uninstall

- **Update:** Quit the app, replace the exe with the new one, and start it. Your settings stay.
- **Uninstall:** turn off **Start with Windows**, Quit, then delete the exe and the `%APPDATA%\PotPlayer TV Brightness` folder.

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| **Connect** is greyed out | It waits for an address: let the search finish and select your TV, or type its IP address. |
| "No TV found" | Is the TV on and on the same network, with no VPN or guest Wi-Fi? Click **Search again**, or type its IP address. |
| "The TV declined" | Click **Connect**, then select **Accept** on the TV. |
| "No answer from … in time" | Click **Connect** and select **Accept** within 60 seconds. |
| "Can't reach a TV at …" | The TV is off or the address is wrong. Type just the address, like `192.168.1.50`. |
| "This TV's firmware blocks the method this app uses" | See Known limitations: the app cannot work with that TV yet. |
| Nothing happens when you start the exe | It is already running. Look for the sun icon, maybe under the **^** arrow. |
| Tooltip says "TV unreachable" | The TV is off, or its address changed: use **Connect TV…**. |
| Nothing happens when playing | Is PotPlayer minimized or paused? Check the log. |
| Brightness goes up and down during a movie | That's **Dark scene brightness**. Set it to Off, or pick a value closer to the movie brightness. |
| Brightness stuck high after a movie | Hover the icon: a pending restore waits for the original picture mode, and switching back to it restores it. Or Quit, set the brightness with the remote, delete `restore.json`, and start the app again. |
| The Accept prompt shows up again | The TV forgot the key, for example after a factory reset. Accept it again. |

## Privacy

The app only talks to your TV on the local network: a search to find it, a request for its name, and the TV's remote API. It sends nothing else anywhere and logs no keys.

With **Dark scene brightness** on, it reads the PotPlayer window from the screen twice a second while a video plays. Each reading is reduced to one number in memory and is never saved or sent; the log keeps only that number at each switch.

## Known limitations

- Windows only. Tested with an LG C2 on webOS 25 and PotPlayer 64-bit.
- Some newer LG firmware blocks the method this app uses (reported on a 2026 C6 with firmware 43.21.60). A firmware update could do the same to older models.
- The exe is not signed, so Windows warns on first run, and a few antivirus products flag it. For v0.1.0, Windows Defender found nothing, and on VirusTotal 2 of 71 engines (Bkav Pro and SecureAge) flag it with generic heuristics that hit many unsigned apps. The release notes link the full report.
- Brightness settings belong to the TV's current input. If you switch the TV to another input or app while a movie is still playing and the movie then ends, the restore writes to that input's picture mode (if the mode name matches).
- A picture mode change in the middle of a movie is not boosted until the next play, or the next dark scene switch.
- Dark scene switches come about 2 seconds after a dark scene starts and about a second after it ends. The cut-offs are fixed, so a very dark film may stay at the dark scene brightness most of the time.
- Dark scenes are not detected if PotPlayer uses exclusive fullscreen or plays protected video (the screen then reads as black), or while another window covers the center of PotPlayer.

## Run from source

For developers, with Python 3.12 and [uv](https://docs.astral.sh/uv/): `uv sync`, then `.venv\Scripts\pythonw.exe run.pyw`. The same Connect window appears on first start.

`uv run python -m scripts.tv_check` reads the TV's picture mode and brightness. `--host <IP>` connects a TV from the command line, and `--set N` writes a brightness (0 to 100), which shows quickly whether a TV accepts the change. Its errors read like `Pairing refused: 403 Error: User rejected pairing` or `Cannot connect to wss://…`.
