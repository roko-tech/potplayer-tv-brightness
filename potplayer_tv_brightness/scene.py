"""How bright is the picture in PotPlayer's window right now?

GDI copies the middle of the window from the screen into a 64x36 bitmap
(StretchBlt), and its pixels are averaged into one number. The edges are left
out because black bars, subtitles, and the player's own controls sit there.
Nothing else is kept: the copy is reduced to that number in memory.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from PIL import Image, ImageStat

SAMPLE = (64, 36)
GA_ROOT = 2
SRCCOPY = 0x00CC0020
COLORONCOLOR = 3  # sample pixels instead of blending them: faster, same average
DIB_RGB_COLORS = 0
# Physical pixels on every monitor, whatever the scaling, for the window's
# position and the screen alike.
PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
user32.SetThreadDpiAwarenessContext.argtypes = [ctypes.c_void_p]
user32.SetThreadDpiAwarenessContext.restype = ctypes.c_void_p
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user32.WindowFromPoint.argtypes = [wintypes.POINT]
user32.WindowFromPoint.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.SetStretchBltMode.argtypes = [wintypes.HDC, ctypes.c_int]
gdi32.StretchBlt.argtypes = [
    wintypes.HDC,
    *(ctypes.c_int,) * 4,
    wintypes.HDC,
    *(ctypes.c_int,) * 4,
    wintypes.DWORD,
]
gdi32.GetDIBits.argtypes = [
    wintypes.HDC,
    wintypes.HBITMAP,
    wintypes.UINT,
    wintypes.UINT,
    ctypes.c_void_p,
    ctypes.POINTER(BITMAPINFOHEADER),
    wintypes.UINT,
]
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wintypes.HDC]


def picture_level(hwnd: int) -> float | None:
    """Average brightness (0-255) of the middle of the window.

    None if the screen cannot be read (for example, while a UAC prompt shows)
    or another window covers the middle of the picture.
    """
    previous = user32.SetThreadDpiAwarenessContext(PER_MONITOR_AWARE_V2)
    try:
        rect = wintypes.RECT()
        origin = wintypes.POINT()
        if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
            return None
        if not user32.ClientToScreen(hwnd, ctypes.byref(origin)):
            return None
        left, top, right, bottom = middle(
            (origin.x, origin.y, origin.x + rect.right, origin.y + rect.bottom)
        )
        if right <= left or bottom <= top:
            return None
        center = wintypes.POINT((left + right) // 2, (top + bottom) // 2)
        if user32.GetAncestor(user32.WindowFromPoint(center), GA_ROOT) != hwnd:
            return None
        pixels = grab((left, top, right, bottom))
        return None if pixels is None else level(pixels)
    finally:
        user32.SetThreadDpiAwarenessContext(previous)


def middle(rect: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """The part of a window that shows picture whatever the video's shape.

    It leaves out 1/8 of the width on each side, which covers 4:3 pillarbox
    bars, and 1/6 of the height at the top and bottom, which covers 2.39:1
    letterbox bars (about 1/8 each), most subtitles, and player controls.
    """
    left, top, right, bottom = rect
    width, height = right - left, bottom - top
    return (
        left + width // 8,
        top + height // 6,
        right - width // 8,
        bottom - height // 6,
    )


def grab(rect: tuple[int, int, int, int]) -> bytes | None:
    """Copy a screen area into SAMPLE as 32-bit BGRX pixels, top row first."""
    left, top, right, bottom = rect
    width, height = SAMPLE
    screen = user32.GetDC(None)
    if not screen:
        return None
    memory = gdi32.CreateCompatibleDC(screen)
    bitmap = gdi32.CreateCompatibleBitmap(screen, width, height)
    try:
        previous = gdi32.SelectObject(memory, bitmap)
        gdi32.SetStretchBltMode(memory, COLORONCOLOR)
        source = (left, top, right - left, bottom - top)
        copied = gdi32.StretchBlt(memory, 0, 0, *SAMPLE, screen, *source, SRCCOPY)
        gdi32.SelectObject(memory, previous)  # GetDIBits needs it unselected
        if not copied:
            return None
        header = BITMAPINFOHEADER(
            biSize=ctypes.sizeof(BITMAPINFOHEADER),
            biWidth=width,
            biHeight=-height,  # negative: top row first
            biPlanes=1,
            biBitCount=32,
        )
        pixels = ctypes.create_string_buffer(width * height * 4)
        rows = gdi32.GetDIBits(
            memory, bitmap, 0, height, pixels, ctypes.byref(header), DIB_RGB_COLORS
        )
        return pixels.raw if rows == height else None
    finally:
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory)
        user32.ReleaseDC(None, screen)


def level(pixels: bytes) -> float:
    """Average luma (0-255) of SAMPLE-sized BGRX pixels."""
    image = Image.frombuffer("RGB", SAMPLE, pixels, "raw", "BGRX", 0, 1)
    return float(ImageStat.Stat(image.convert("L")).mean[0])
