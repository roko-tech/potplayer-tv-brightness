"""Find LG webOS TVs on the local network with SSDP, the way LG's phone app does.

A PC often has several network adapters (VPN, WSL, Hyper-V), and the search
only works on the one the TV is on, so it is sent from every IPv4 address.
Replies are untrusted: the TV's name is only read from the address that
replied, over plain HTTP with a short time budget and a size cap.
"""

from __future__ import annotations

import html
import http.client
import re
import select
import socket
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

SSDP_TARGET = ("239.255.255.250", 1900)
SEARCH = (
    b"M-SEARCH * HTTP/1.1\r\n"
    b"HOST: 239.255.255.250:1900\r\n"
    b'MAN: "ssdp:discover"\r\n'
    b"MX: 2\r\n"
    b"ST: urn:lge-com:service:webos-second-screen:1\r\n\r\n"
)
LOCATION = re.compile(rb"^location:[ \t]*(\S+)", re.IGNORECASE | re.MULTILINE)
FRIENDLY_NAME = re.compile(rb"<friendlyName>([^<]{1,100})</friendlyName>")
UNNAMED = "LG TV"


@dataclass(frozen=True)
class FoundTV:
    host: str
    name: str


def find_tvs(timeout: float = 3.0) -> list[FoundTV]:
    """LG TVs that answer within ``timeout`` seconds, in the order they replied."""
    sockets = []
    for address in _local_addresses():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            sock.bind((address, 0))
            sock.setsockopt(
                socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(address)
            )
            sock.sendto(SEARCH, SSDP_TARGET)
        except OSError:  # an adapter that is down or cannot multicast
            sock.close()
            continue
        sockets.append(sock)

    replies: dict[str, bytes] = {}
    deadline = time.monotonic() + timeout
    try:
        while sockets and (left := deadline - time.monotonic()) > 0:
            ready, _, _ = select.select(sockets, [], [], left)
            for sock in ready:
                try:
                    reply, (host, _) = sock.recvfrom(4096)
                except OSError:
                    sockets.remove(sock)
                    sock.close()
                    continue
                if b"webos-second-screen" in reply:
                    replies.setdefault(host, reply)
    finally:
        for sock in sockets:
            sock.close()
    return [FoundTV(host, _name(host, reply)) for host, reply in replies.items()]


def _local_addresses() -> list[str]:
    try:
        infos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
    except OSError:
        infos = []
    return sorted({str(info[4][0]) for info in infos}) or ["0.0.0.0"]


def _name(host: str, reply: bytes) -> str:
    """The TV's name from its UPnP description, if the replying host serves it."""
    match = LOCATION.search(reply)
    try:
        url = urlsplit(match.group(1).decode("latin-1")) if match else None
        if not url or url.scheme != "http" or url.hostname != host:
            return UNNAMED
        connection = http.client.HTTPConnection(host, url.port or 80, timeout=1)
        try:
            connection.request("GET", url.path or "/")
            response = connection.getresponse()
            body, deadline = b"", time.monotonic() + 2
            while len(body) < 65536 and time.monotonic() < deadline:
                chunk = response.read1(4096)
                if not chunk:
                    break
                body += chunk
        finally:
            connection.close()
    except (OSError, ValueError, http.client.HTTPException):
        return UNNAMED
    name = FRIENDLY_NAME.search(body)
    if not name:
        return UNNAMED
    return html.unescape(name.group(1).decode("utf-8", "replace")).strip()
