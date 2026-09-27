# ADR-0004: Ship a single-file exe with a first-run Connect window

- Date: 2026-09-27
- Status: Accepted
- Owners: @rokogan
- Related: [ADR-0002](0002-control-tv-brightness-over-webos-ssap.md), [product brief](../../product/brief.md)

## Context

The app ran from source only: Python 3.12, uv, Git, and a command to connect the TV by its IP address. The owner asked for an exe that a normal user can run. Such a user has no Python and no terminal, and finding the TV's IP in its menus is a hurdle. The brief listed "a packaged executable" and "auto-discovery of the TV" as non-goals; this decision reverses both.

## Decision drivers

- Download and run: no Python, terminal, installer, or admin rights.
- The TV should be found without typing an address.
- Keep the owner's source setup working unchanged.
- Small code and no paid services.

## Considered options

### PyInstaller, one file (chosen)

One exe of about 19 MB that unpacks itself to a temporary folder at start (about a second). PyInstaller's license (GPL with a bundling exception) allows shipping the MIT app. It is a build-only dependency.

### PyInstaller, one folder in a zip

Starts faster, but the user has to unzip and find the exe among many files.

### Nuitka

Compiles to C and may trigger fewer antivirus false positives, but needs a C toolchain download of several hundred MB and builds far more slowly.

### An MSI installer

Adds a Start menu entry and an uninstall entry, but needs more tooling and is still unsigned.

## Decision

- **Build:** `packaging\build.cmd` builds PyInstaller from its hash-pinned source with the launcher compiled locally (Visual Studio Build Tools), then builds from `packaging/potplayer-tv-brightness.spec`. PyInstaller sits in its own `build` dependency group so normal syncs and CI do not install it. Windowed, no UPX (it raises antivirus false positives), with the icon drawn from the tray icon at build time. On VirusTotal the same exe drew 4 of 71 detections with the stock launcher and 2 of 71 (Bkav Pro, SecureAge) with a locally compiled one.
- **First run:** a Tk window finds LG TVs with an SSDP search sent from every IPv4 address (VPN and virtual adapters otherwise swallow it), lists them by name, and pairs on Connect. Typing the IP stays as a fallback. The address is saved only after the TV answers. The tray menu's **Connect TV…** reopens the window on its own thread, since pystray runs menu actions on the tray thread.
- **Files:** `%APPDATA%\PotPlayer TV Brightness` when packaged; the repository folder when run from source, as before.
- **Start with Windows:** a tray toggle that writes the per-user `Run` registry key, which needs no admin rights.
- **Releases:** immutable GitHub releases (tag and files locked after publishing, with a GitHub-signed attestation), each with the exe, `SHA256SUMS.txt`, and `THIRD-PARTY-NOTICES.txt` generated from the bundled packages' license files. pystray is LGPL-3.0; the public source and build steps let anyone rebuild with a modified copy. The exe name has no spaces (GitHub turns them into dots), and its version info comes from `pyproject.toml`.
- **Signing:** none for now. Windows SmartScreen warns on first run; the docs say how to continue. Since 2024 even EV certificates no longer skip SmartScreen's reputation check. SignPath Foundation signs open-source projects for free once the repository is public and builds in CI; Azure Artifact Signing is limited to individuals in the US and Canada.

## Consequences

### Positive

- A normal user downloads one file, clicks Connect, and accepts on the TV.
- The source setup and `tv_check` keep working for development.

### Negative and tradeoffs

- The unsigned exe shows a SmartScreen warning, and antivirus products may flag PyInstaller exes. Windows Defender found nothing in the first build.
- Each release needs a Windows build. Source and exe keep separate files, so switching between them means connecting once more.
- The SSDP search and the name lookup are new network traffic on the LAN (see the threat model).

## Validation

Unit tests cover the search against a fake TV on localhost, the Connect window (driven hidden), the first-run start of the tray, the `Run` key toggle, and the packaged file location. The exe was run end to end on the owner's PC; see [testing](../../testing.md).
