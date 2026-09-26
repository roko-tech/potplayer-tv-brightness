from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

import websocket

from potplayer_tv_brightness.controller import Picture, TVError
from potplayer_tv_brightness.tv import LGTV

REGISTERED = {"type": "registered", "id": "register", "payload": {"client-key": "k1"}}


class FakeWebSocket:
    """Replays scripted TV messages and records what the client sent."""

    def __init__(self, replies: list[dict[str, Any]]) -> None:
        self.replies = list(replies)
        self.sent: list[dict[str, Any]] = []
        self.timeouts: list[float] = []
        self.closed = False
        self.connect_kwargs: dict[str, Any] = {}

    def send(self, text: str) -> None:
        self.sent.append(json.loads(text))

    def recv(self) -> str:
        if not self.replies:
            raise websocket.WebSocketTimeoutException("timed out")
        return json.dumps(self.replies.pop(0))

    def settimeout(self, timeout: float) -> None:
        self.timeouts.append(timeout)

    def close(self) -> None:
        self.closed = True


class LGTVTest(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.key_file = Path(folder.name) / "tv-client-key.txt"

    def tv(self, ws: FakeWebSocket) -> LGTV:
        def connect(url: str, **kwargs: Any) -> FakeWebSocket:
            ws.connect_kwargs = {"url": url, **kwargs}
            return ws

        return LGTV("tv.local", self.key_file, connect=connect)

    def test_reads_picture_with_the_saved_key(self) -> None:
        self.key_file.write_text("k1", encoding="utf-8")
        reply = {
            "returnValue": True,
            "settings": {"pictureMode": "normal", "backlight": 20},
        }
        ws = FakeWebSocket(
            [REGISTERED, {"type": "response", "id": "1", "payload": reply}]
        )
        with self.tv(ws).session() as session:
            self.assertEqual(session.read_picture(), Picture("normal", 20))

        self.assertEqual(ws.sent[0]["payload"]["client-key"], "k1")
        self.assertEqual(
            ws.sent[1],
            {
                "type": "request",
                "id": "1",
                "uri": "ssap://settings/getSystemSettings",
                "payload": {
                    "category": "picture",
                    "keys": ["pictureMode", "backlight"],
                },
            },
        )
        self.assertTrue(ws.closed)
        self.assertEqual(ws.connect_kwargs["url"], "wss://tv.local:3001")
        self.assertTrue(ws.connect_kwargs["suppress_origin"])  # webOS requires it

    def test_set_backlight_writes_the_picture_setting(self) -> None:
        self.key_file.write_text("k1", encoding="utf-8")
        ok = {"type": "response", "id": "1", "payload": {"returnValue": True}}
        ws = FakeWebSocket([REGISTERED, ok])
        with self.tv(ws).session() as session:
            session.set_backlight(80)
        self.assertEqual(ws.sent[1]["uri"], "ssap://settings/setSystemSettings")
        self.assertEqual(
            ws.sent[1]["payload"],
            {"category": "picture", "settings": {"backlight": 80}},
        )

    def test_first_use_pairs_and_saves_the_key(self) -> None:
        prompt = {
            "type": "response",
            "id": "register",
            "payload": {"pairingType": "PROMPT", "returnValue": True},
        }
        registered = {**REGISTERED, "payload": {"client-key": "new-key"}}
        ws = FakeWebSocket([prompt, registered])
        with self.tv(ws).session():
            pass
        self.assertNotIn("client-key", ws.sent[0]["payload"])
        self.assertEqual(self.key_file.read_text(encoding="utf-8"), "new-key")
        self.assertEqual(ws.timeouts, [60.0, 3.0])  # waits for Accept, then normal

    def test_refused_pairing_raises(self) -> None:
        ws = FakeWebSocket([{"type": "error", "id": "register", "error": "denied"}])
        with self.assertRaises(TVError), self.tv(ws).session():
            pass
        self.assertTrue(ws.closed)
        self.assertFalse(self.key_file.exists())

    def test_rejected_request_raises(self) -> None:
        rejected = {"type": "error", "id": "1", "error": "401 insufficient permissions"}
        ws = FakeWebSocket([REGISTERED, rejected])
        with self.assertRaises(TVError), self.tv(ws).session() as session:
            session.set_backlight(80)

    def test_false_return_value_raises(self) -> None:
        failed = {"type": "response", "id": "1", "payload": {"returnValue": False}}
        ws = FakeWebSocket([REGISTERED, failed])
        with self.assertRaises(TVError), self.tv(ws).session() as session:
            session.set_backlight(80)

    def test_unrelated_messages_are_skipped(self) -> None:
        other = {"type": "response", "id": "99", "payload": {"returnValue": False}}
        ok = {"type": "response", "id": "1", "payload": {"returnValue": True}}
        ws = FakeWebSocket([REGISTERED, other, ok])
        with self.tv(ws).session() as session:
            session.set_backlight(80)

    def test_malformed_picture_reply_raises(self) -> None:
        reply = {"returnValue": True, "settings": {"pictureMode": "normal"}}
        ws = FakeWebSocket(
            [REGISTERED, {"type": "response", "id": "1", "payload": reply}]
        )
        with self.assertRaises(TVError), self.tv(ws).session() as session:
            session.read_picture()

    def test_silent_tv_raises_and_closes(self) -> None:
        ws = FakeWebSocket([])
        with self.assertRaises(TVError), self.tv(ws).session():
            pass
        self.assertTrue(ws.closed)

    def test_malformed_address_raises(self) -> None:
        tv = LGTV("192.168.1.50:3001", self.key_file)  # fails before any network
        with self.assertRaises(TVError), tv.session():
            pass

    def test_unreachable_tv_raises(self) -> None:
        def refuse(url: str, **kwargs: Any) -> FakeWebSocket:
            raise ConnectionRefusedError("refused")

        tv = LGTV("tv.local", self.key_file, connect=refuse)
        with self.assertRaises(TVError), tv.session():
            pass


if __name__ == "__main__":
    unittest.main()
