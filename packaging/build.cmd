@echo off
rem Builds the release files in dist\ (see packaging\potplayer-tv-brightness.spec).
rem
rem PyInstaller is built from its hash-pinned source with its launcher compiled
rem here: exes using the stock launcher get about twice as many antivirus false
rem alarms. Needs Visual Studio Build Tools with the "Desktop development with
rem C++" workload.
setlocal
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
for /f "usebackq delims=" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VS=%%i"
if not defined VS (
    echo Visual Studio C++ build tools not found.
    exit /b 1
)
call "%VS%\VC\Auxiliary\Build\vcvars64.bat" >nul || exit /b 1

rem The launcher build fails when TEMP mixes short and long folder names.
cd /d "%~dp0.."
if not exist build\tmp mkdir build\tmp
set "TEMP=%CD%\build\tmp"
set "TMP=%CD%\build\tmp"
set PYINSTALLER_COMPILE_BOOTLOADER=1

uv sync --group build --locked --no-binary-package pyinstaller --reinstall-package pyinstaller --no-cache || exit /b 1
uv run --group build --no-sync pyinstaller --noconfirm --clean packaging\potplayer-tv-brightness.spec || exit /b 1
