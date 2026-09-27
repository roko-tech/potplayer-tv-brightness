# PyInstaller build of "dist/PotPlayer TV Brightness.exe": one file, no console.
#
#     uv run --group build pyinstaller --noconfirm --clean packaging/potplayer-tv-brightness.spec
#
# The exe icon is drawn from the tray icon, so there is no binary to keep in Git.
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
sys.path.insert(0, str(ROOT))
from potplayer_tv_brightness.app import APP_NAME, icon_image  # noqa: E402

icon = Path(workpath) / "icon.ico"
icon.parent.mkdir(parents=True, exist_ok=True)
icon_image(True).save(icon, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)])

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
    name=APP_NAME,
    console=False,
    icon=str(icon),
    upx=False,  # UPX-packed exes trigger more antivirus false positives
)
