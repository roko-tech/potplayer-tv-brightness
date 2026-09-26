# Backup and restore plan

- Status: Not applicable (no backups needed)
- Owner: @rokogan
- Last successful restore rehearsal: Not applicable

The app keeps no data worth backing up. Everything can be recreated in a minute:

| Data/system | If lost | Recovery |
| --- | --- | --- |
| `settings.json` | Defaults are recreated on the next start | Pick the movie brightness again in the tray; fix `tv_host` if needed |
| `tv-client-key.txt` | The TV asks to pair again | Accept the prompt on the TV |
| `restore.json` | The TV may stay at movie brightness | Set the desktop value with `uv run python -m scripts.tv_check --set N` or the remote |
| Source code | GitHub repository | `git clone` |

The TV's own picture settings are the TV's responsibility and are not backed up by this app.
