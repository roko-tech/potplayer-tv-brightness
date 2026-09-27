"""The "Connect your TV" window: find the TV, pair with it, return its address.

It runs its own Tk loop in the calling thread. Searching and pairing happen on
worker threads that hand results back through a queue, so the window stays
responsive while the TV waits (up to 60 s) for the user to select Accept.
"""

from __future__ import annotations

import base64
import io
import queue
import threading
import tkinter as tk
from collections.abc import Callable
from functools import partial
from pathlib import Path
from tkinter import ttk

from PIL import Image

from .controller import TVError
from .discovery import FoundTV, find_tvs
from .tv import LGTV

TITLE = "PotPlayer TV Brightness"
WRAP = 380  # status text width in pixels


def explain(error: TVError, host: str) -> str:
    """A short, actionable message for a failed connection."""
    text = str(error)
    if "blacklisted" in text or "401" in text:
        return (
            "This TV's firmware blocks the method this app uses, "
            "so it cannot work with this TV yet."
        )
    if "Pairing refused" in text:
        return "The TV declined. Click Connect, then select Accept on the TV."
    if "timed out" in text:
        return (
            f"No answer from {host} in time. If the TV asked to allow the "
            "connection, click Connect and select Accept within 60 seconds."
        )
    return (
        f"Can't reach a TV at {host}. Check that the TV is on and on the same "
        "network as this PC."
    )


def connect_dialog(host: str, key_file: Path, icon: Image.Image) -> str | None:
    """Show the window. Returns the connected TV's address, or None if closed."""
    return ConnectWindow(host, key_file, icon).run()


class ConnectWindow:
    def __init__(self, host: str, key_file: Path, icon: Image.Image) -> None:
        self.key_file = key_file
        self.connected: str | None = None
        self.found: list[FoundTV] = []
        self.results: queue.Queue[Callable[[], None]] = queue.Queue()

        self.root = root = tk.Tk()
        root.title(TITLE)
        root.resizable(False, False)
        png = io.BytesIO()
        icon.save(png, "PNG")
        self.icon = tk.PhotoImage(data=base64.b64encode(png.getvalue()))
        root.iconphoto(True, self.icon)
        frame = ttk.Frame(root, padding=16)
        frame.grid()
        title = ttk.Label(
            frame, text="Connect your LG TV", font=("Segoe UI", 12, "bold")
        )
        title.grid(sticky="w")
        ttk.Label(
            frame,
            text="Turn the TV on. It must be on the same network as this PC.",
            wraplength=WRAP,
        ).grid(sticky="w", pady=(4, 10))
        self.tv_list = tk.Listbox(frame, height=4, activestyle="none")
        self.tv_list.grid(sticky="we")
        self.tv_list.bind("<<ListboxSelect>>", lambda _: self._pick())
        row = ttk.Frame(frame)
        row.grid(sticky="we", pady=(8, 0))
        ttk.Label(row, text="IP address:").pack(side="left")
        self.address = tk.StringVar(value=host)
        ttk.Entry(row, textvariable=self.address, width=18).pack(side="left", padx=6)
        self.search_button = ttk.Button(row, text="Search again", command=self._search)
        self.search_button.pack(side="right")
        self.status = tk.StringVar()
        status = ttk.Label(frame, textvariable=self.status, wraplength=WRAP)
        status.grid(sticky="w", pady=(12, 0))
        buttons = ttk.Frame(frame)
        buttons.grid(sticky="e", pady=(12, 0))
        self.connect_button = ttk.Button(buttons, text="Connect", command=self._connect)
        self.connect_button.pack(side="left")
        cancel = ttk.Button(buttons, text="Cancel", command=root.destroy)
        cancel.pack(side="left", padx=(6, 0))
        root.bind("<Return>", lambda _: self._connect())

        root.update_idletasks()  # center it, and bring it to the front
        x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
        y = (root.winfo_screenheight() - root.winfo_reqheight()) // 3
        root.geometry(f"+{x}+{y}")
        root.attributes("-topmost", True)
        root.after(500, lambda: root.attributes("-topmost", False))
        root.focus_force()

        root.after(100, self._drain)
        self._search()

    def run(self) -> str | None:
        self.root.mainloop()
        self.close()
        return self.connected

    def close(self) -> None:
        """Cancel pending timers (Tcl reports them later otherwise), then destroy."""
        try:
            for pending in self.root.tk.splitlist(self.root.tk.call("after", "info")):
                self.root.after_cancel(pending)
            self.root.destroy()
        except tk.TclError:
            pass  # already closed with Cancel or the X button

    def _in_background(self, work: Callable[[], Callable[[], None]]) -> None:
        """Run work on a thread; the callback it returns runs on the Tk thread."""

        def run() -> None:
            try:
                done = work()
            except Exception as error:  # show it rather than hang the window
                done = partial(self._failed, f"Unexpected error: {error}")
            self.results.put(done)

        threading.Thread(target=run, daemon=True).start()

    def _drain(self) -> None:
        while not self.results.empty():
            self.results.get()()
        self.root.after(100, self._drain)

    def _search(self) -> None:
        self.search_button.state(["disabled"])
        self.status.set("Searching for LG TVs…")

        def work() -> Callable[[], None]:
            return partial(self._show, find_tvs())

        self._in_background(work)

    def _show(self, tvs: list[FoundTV]) -> None:
        self.search_button.state(["!disabled"])
        self.found = tvs
        self.tv_list.delete(0, "end")
        for tv in tvs:
            self.tv_list.insert("end", f"{tv.name}    {tv.host}")
        if not tvs:
            self.status.set(
                "No TV found. Check that it is on and on this network, or type "
                "its IP address (on the TV: Settings > General > Network)."
            )
            return
        if not self.address.get().strip():
            self.tv_list.selection_set(0)
            self._pick()
        self.status.set("Select your TV and click Connect.")

    def _pick(self) -> None:
        for index, tv in enumerate(self.found):
            if self.tv_list.selection_includes(index):
                self.address.set(tv.host)

    def _connect(self) -> None:
        host = self.address.get().strip()
        if self.connect_button.instate(["disabled"]):
            return  # already connecting
        if not host:
            self.status.set("Select your TV or type its IP address.")
            return
        self.connect_button.state(["disabled"])
        self.status.set(
            "Connecting… If the TV asks to allow the connection, "
            "select Accept with the remote."
        )

        def work() -> Callable[[], None]:
            try:
                with LGTV(host, self.key_file).session() as tv:
                    tv.read_picture()
            except TVError as error:
                return partial(self._failed, explain(error, host))
            return partial(self._done, host)

        self._in_background(work)

    def _failed(self, message: str) -> None:
        self.connect_button.state(["!disabled"])
        self.search_button.state(["!disabled"])
        self.status.set(message)

    def _done(self, host: str) -> None:
        self.connected = host
        self.root.quit()
