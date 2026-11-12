"""LG webOS TV adapter: read the picture mode and set OLED Pixel Brightness.

Talks SSAP (JSON over a TLS WebSocket on port 3001). The TV accepts
``ssap://settings/setSystemSettings`` for the picture category because the
standard signed LG manifest in ``pairing.json`` (copied from the lgtv2 package)
grants ``WRITE_SETTINGS``. Verified on an LG C2 running webOS 25.

LG firmware from 2026 on rejects that signature as blacklisted. The session
then pairs without it and writes through a notification alert instead; see
ADR-0006. Verified on the same C2 on 2026-11-12, after a firmware update.

Each session is a short-lived connection, so a TV that was switched off or
rebooted in between needs no reconnect logic.
"""

from __future__ import annotations

import json
import ssl
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import websocket

from .controller import Picture, TVError

PAIRING: dict[str, Any] = json.loads(
    Path(__file__).with_name("pairing.json").read_text(encoding="utf-8")
)
# The same manifest without the signature, asking for all of its permissions.
# The TV grants it READ_SETTINGS and WRITE_NOTIFICATION_ALERT, not WRITE_SETTINGS.
UNSIGNED_MANIFEST: dict[str, Any] = {
    key: value
    for key, value in PAIRING["manifest"].items()
    if key not in ("signatures", "signed")
}
UNSIGNED_MANIFEST["permissions"] = sorted(
    {*PAIRING["manifest"]["permissions"], *PAIRING["manifest"]["signed"]["permissions"]}
)
LUNA_SET_SETTINGS = "luna://com.webos.settingsservice/setSystemSettings"
# The TV's certificate is self-signed, so it cannot be verified. This applies
# to this connection only; see docs/security/threat-model.md.
SSL_OPTIONS = {"cert_reqs": ssl.CERT_NONE, "check_hostname": False}
CONNECTION_ERRORS = (OSError, websocket.WebSocketException)


class LGTV:
    def __init__(
        self,
        host: str,
        key_file: Path,
        *,
        timeout: float = 3.0,
        pair_timeout: float = 60.0,
        connect: Callable[..., Any] = websocket.create_connection,
    ) -> None:
        self.url = f"wss://{host}:3001"
        self.key_file = key_file
        self.timeout = timeout
        self.pair_timeout = pair_timeout
        self._connect = connect

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        try:
            # webOS closes the socket ("invalid origin") if an Origin header is sent.
            ws = self._connect(
                self.url, timeout=self.timeout, sslopt=SSL_OPTIONS, suppress_origin=True
            )
        except (*CONNECTION_ERRORS, ValueError) as error:  # ValueError: bad address
            raise TVError(f"Cannot connect to {self.url}: {error}") from error
        try:
            session = Session(ws)
            session.register(self.key_file, self.timeout, self.pair_timeout)
            yield session
        finally:
            ws.close()


class Session:
    """One registered connection to the TV."""

    def __init__(self, ws: Any) -> None:
        self.ws = ws
        self.signed = True  # until the TV rejects LG's signature
        self._last_id = 0

    def register(self, key_file: Path, timeout: float, pair_timeout: float) -> None:
        """Authenticate with the saved client key, or pair on first use.

        Pairing shows an Accept prompt on the TV; the key it returns is saved.
        A blacklisted signature is retried once, unsigned, on the same socket.
        """
        key = key_file.read_text(encoding="utf-8").strip() if key_file.exists() else ""
        payload = dict(PAIRING, **({"client-key": key} if key else {}))
        self._send({"type": "register", "id": "register", "payload": payload})
        while True:
            message = self._receive()
            body = message.get("payload")
            body = body if isinstance(body, dict) else {}
            if message.get("type") == "registered":
                new_key = str(body.get("client-key", ""))
                if new_key and new_key != key:
                    key_file.write_text(new_key, encoding="utf-8")
                self.ws.settimeout(timeout)
                return
            if message.get("type") == "error":
                error = str(message.get("error"))
                if self.signed and "blacklisted" in error:
                    self.signed = False
                    payload["manifest"] = UNSIGNED_MANIFEST
                    self._send(
                        {"type": "register", "id": "register", "payload": payload}
                    )
                    continue
                raise TVError(f"Pairing refused: {error}")
            if body.get("pairingType") == "PROMPT":
                self.ws.settimeout(pair_timeout)  # give the user time to accept

    def read_picture(self) -> Picture:
        reply = self._request(
            "ssap://settings/getSystemSettings",
            {"category": "picture", "keys": ["pictureMode", "backlight"]},
        )
        try:
            settings = reply["settings"]
            return Picture(str(settings["pictureMode"]), int(settings["backlight"]))
        except (KeyError, TypeError, ValueError) as error:
            raise TVError(f"Unexpected picture settings reply: {reply}") from error

    def set_backlight(self, value: int) -> None:
        settings = {"category": "picture", "settings": {"backlight": value}}
        if self.signed:
            self._request("ssap://settings/setSystemSettings", settings)
            return
        # Unsigned clients may not write settings, but may show alerts. Closing
        # this one makes the TV run its onclose luna call with its own rights.
        # The payload is bscpylgtv's; the TV does not report the call's result.
        call = {"uri": LUNA_SET_SETTINGS, "params": settings}
        alert = self._request(
            "ssap://system.notifications/createAlert",
            {
                "message": " ",
                "buttons": [
                    {"label": "", "onClick": LUNA_SET_SETTINGS, "params": settings}
                ],
                "onclose": call,
                "onfail": call,
            },
        )
        self._request(
            "ssap://system.notifications/closeAlert", {"alertId": alert.get("alertId")}
        )

    def _request(self, uri: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._last_id += 1
        request_id = str(self._last_id)
        self._send(
            {"type": "request", "id": request_id, "uri": uri, "payload": payload}
        )
        while True:
            message = self._receive()
            if message.get("id") != request_id:
                continue
            reply = message.get("payload")
            if (
                message.get("type") == "error"
                or not isinstance(reply, dict)
                or reply.get("returnValue") is False
            ):
                raise TVError(f"{uri} failed: {message.get('error') or reply}")
            return reply

    def _send(self, message: dict[str, Any]) -> None:
        try:
            self.ws.send(json.dumps(message))
        except CONNECTION_ERRORS as error:
            raise TVError(f"TV connection failed: {error}") from error

    def _receive(self) -> dict[str, Any]:
        try:
            message = json.loads(self.ws.recv())
        except (*CONNECTION_ERRORS, ValueError) as error:
            raise TVError(f"TV connection failed: {error}") from error
        if not isinstance(message, dict):
            raise TVError(f"Unexpected TV message: {message!r}")
        return message
