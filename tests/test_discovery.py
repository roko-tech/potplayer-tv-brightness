from __future__ import annotations

import socket
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from potplayer_tv_brightness import discovery
from potplayer_tv_brightness.discovery import FoundTV

DESCRIPTION = b"""<?xml version="1.0"?>
<root><device><friendlyName>[LG] webOS TV OLED48C2</friendlyName></device></root>"""


class FakeTV:
    """Answers SSDP searches on localhost (twice, like a real TV) and serves
    a UPnP description."""

    def __init__(self, location_host: str = "127.0.0.1", st: str = "") -> None:
        self.requests = 0
        fake = self

        class Description(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                fake.requests += 1
                self.send_response(200)
                self.end_headers()
                self.wfile.write(DESCRIPTION)

            def log_message(self, format: str, *args: object) -> None:
                pass

        self.http = HTTPServer(("127.0.0.1", 0), Description)
        port = self.http.server_address[1]
        st = st or "urn:lge-com:service:webos-second-screen:1"
        self.reply = (
            "HTTP/1.1 200 OK\r\n"
            f"Location: http://{location_host}:{port}/\r\n"
            f"ST: {st}\r\n\r\n"
        ).encode()
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.bind(("127.0.0.1", 0))
        self.address = self.udp.getsockname()
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        threading.Thread(target=self._answer, daemon=True).start()

    def _answer(self) -> None:
        while True:
            try:
                data, sender = self.udp.recvfrom(4096)
            except OSError:
                return  # closed
            if data.startswith(b"M-SEARCH"):
                self.udp.sendto(self.reply, sender)
                self.udp.sendto(self.reply, sender)

    def close(self) -> None:
        self.udp.close()
        self.http.shutdown()
        self.http.server_close()


class FindTVsTest(unittest.TestCase):
    def find(self, tv: FakeTV) -> list[FoundTV]:
        self.addCleanup(tv.close)
        with (
            mock.patch.object(
                discovery, "_local_addresses", return_value=["127.0.0.1"]
            ),
            mock.patch.object(discovery, "SSDP_TARGET", tv.address),
        ):
            return discovery.find_tvs(timeout=1)

    def test_finds_a_tv_and_reads_its_name(self) -> None:
        tv = FakeTV()
        found = self.find(tv)
        self.assertEqual(found, [FoundTV("127.0.0.1", "[LG] webOS TV OLED48C2")])
        self.assertEqual(tv.requests, 1)  # the duplicate reply is not fetched again

    def test_name_is_only_read_from_the_replying_host(self) -> None:
        tv = FakeTV(location_host="localhost")  # points away from 127.0.0.1
        self.assertEqual(self.find(tv), [FoundTV("127.0.0.1", "LG TV")])
        self.assertEqual(tv.requests, 0)

    def test_other_devices_are_ignored(self) -> None:
        tv = FakeTV(st="urn:schemas-upnp-org:device:InternetGatewayDevice:1")
        self.assertEqual(self.find(tv), [])


if __name__ == "__main__":
    unittest.main()
