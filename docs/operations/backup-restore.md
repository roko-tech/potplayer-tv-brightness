# Backup and restore plan

- Status: Not applicable (no backups needed)
- Owner: @rokogan
- Last successful restore rehearsal: Not applicable

The app keeps no data worth backing up. Everything can be recreated in a minute. The exe keeps its files in `%APPDATA%\PotPlayer TV Brightness`; from source they are in the repository folder.

| Data/system | If lost | Recovery |
| --- | --- | --- |
| `settings.json` | The Connect window appears on the next start | Connect again and pick the movie brightness in the tray |
| `tv-client-key.txt` | The TV asks to pair again | Accept the prompt on the TV |
| `restore.json` | The TV may stay at movie brightness | Set the desktop value with the remote (or `tv_check --set N` from source) |
| Source code | GitHub repository | `git clone` |

The TV's own picture settings are the TV's responsibility and are not backed up by this app.
