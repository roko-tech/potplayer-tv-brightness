# PyInstaller build of the release files in dist/: PotPlayer-TV-Brightness.exe
# (one file, no console), THIRD-PARTY-NOTICES.txt, and SHA256SUMS.txt.
#
#     uv run --group build pyinstaller --noconfirm --clean packaging/potplayer-tv-brightness.spec
#
# The exe icon is drawn from the tray icon, so there is no binary to keep in Git.
import hashlib
import sys
import tomllib
from importlib.metadata import distribution
from pathlib import Path

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

ROOT = Path(SPECPATH).parent
sys.path.insert(0, str(ROOT))
from potplayer_tv_brightness.app import APP_NAME, icon_image  # noqa: E402

EXE_NAME = "PotPlayer-TV-Brightness"  # no spaces: GitHub turns them into dots
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))["project"]["version"]
REPOSITORY = "https://github.com/roko-tech/potplayer-tv-brightness"
BUNDLED = ("pystray", "pillow", "websocket-client", "six", "pyinstaller")

icon = Path(workpath) / "icon.ico"
icon.parent.mkdir(parents=True, exist_ok=True)
icon_image(True).save(icon, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)])

numbers = (*(int(part) for part in VERSION.split(".")), 0)  # 0.1.0 -> 0.1.0.0
version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=numbers, prodvers=numbers),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("CompanyName", "rokogan"),
                        StringStruct("FileDescription", APP_NAME),
                        StringStruct("FileVersion", VERSION),
                        StringStruct("InternalName", EXE_NAME),
                        StringStruct("LegalCopyright", "Copyright (c) 2026 rokogan. MIT License."),
                        StringStruct("OriginalFilename", f"{EXE_NAME}.exe"),
                        StringStruct("ProductName", APP_NAME),
                        StringStruct("ProductVersion", VERSION),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [0x0409, 1200])]),
    ],
)

a = Analysis(
    [str(ROOT / "run.pyw")],
    pathex=[str(ROOT)],
    datas=[
        (str(ROOT / "potplayer_tv_brightness" / "pairing.json"), "potplayer_tv_brightness"),
    ],
    hiddenimports=["pystray._win32"],  # pystray picks its backend at runtime
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name=EXE_NAME,
    console=False,
    icon=str(icon),
    version=version_info,
    upx=False,  # UPX-packed exes trigger more antivirus false positives
)

# License texts for everything bundled in the exe. pystray is LGPL-3.0: the
# statement below and the public source satisfy its rebuild ("relink") terms.
sections = [
    f"{APP_NAME} {VERSION} bundles Python and the libraries below.\n"
    f"Source code and build instructions: {REPOSITORY}\n\n"
    "pystray is licensed under the GNU LGPL v3. To use a modified pystray, install\n"
    "your version into the build environment and rebuild the exe with the command\n"
    "in the README. The full LGPL and GPL texts follow in the pystray section.",
    f"Python {sys.version.split()[0]} and the libraries it bundles (OpenSSL, libffi,\n"
    "Tcl/Tk, and others)\n\n"
    + (Path(sys.base_prefix) / "LICENSE.txt").read_text("utf-8", errors="replace"),
]
for name in BUNDLED:
    package = distribution(name)
    for file in package.files or []:
        if any(word in file.name.upper() for word in ("LICENSE", "LICENCE", "COPYING")):
            text = Path(file.locate()).read_text("utf-8", errors="replace")
            sections.append(f"{name} {package.version} ({file.name})\n\n{text}")
notices = Path(DISTPATH) / "THIRD-PARTY-NOTICES.txt"
notices.write_bytes(("\n\n" + "=" * 78 + "\n\n").join(sections).encode())  # LF

# `sha256sum -c SHA256SUMS.txt` needs LF line endings, so write bytes.
sums = [
    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
    for path in (Path(DISTPATH) / f"{EXE_NAME}.exe", notices)
]
(Path(DISTPATH) / "SHA256SUMS.txt").write_bytes(("\n".join(sums) + "\n").encode())
