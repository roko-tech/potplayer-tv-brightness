"""Is PotPlayer playing something the user can see?

Uses PotPlayer's window-message API: sending WM_USER with 0x5006 to the main
window returns the play state (-1 idle, 1 paused, 2 playing), as validated
against stock PotPlayerMini64 in D:/MyScripts/potplayer/potplayer_api.py.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

WM_USER = 0x0400
POT_GET_PLAY_STATE = 0x5006
PLAYING = 2
SMTO_ABORTIFHUNG = 0x0002
WINDOW_CLASSES = ("PotPlayer64", "PotPlayer")  # 64-bit and 32-bit main windows

user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.SendMessageTimeoutW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
    wintypes.UINT,
    wintypes.UINT,
    ctypes.POINTER(wintypes.LPARAM),
]
user32.SendMessageTimeoutW.restype = wintypes.LPARAM


def _player_windows() -> list[int]:
    found: list[int] = []
    name = ctypes.create_unicode_buffer(64)

    def collect(hwnd: int, _: int) -> bool:
        if user32.GetClassNameW(hwnd, name, len(name)) and name.value in WINDOW_CLASSES:
            found.append(hwnd)
        return True

    user32.EnumWindows(EnumWindowsProc(collect), 0)
    return found


def is_watching() -> bool:
    """True if a PotPlayer window is playing and is not minimized or hidden."""
    for hwnd in _player_windows():
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
            continue
        state = wintypes.LPARAM()
        answered = user32.SendMessageTimeoutW(
            hwnd,
            WM_USER,
            POT_GET_PLAY_STATE,
            0,
            SMTO_ABORTIFHUNG,
            500,
            ctypes.byref(state),
        )
        if answered and state.value == PLAYING:
            return True
    return False
