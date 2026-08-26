from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable, Generator
from typing import Any

import pytest


def _is_loopback_host(host: object) -> bool:
    if not isinstance(host, str):
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


@pytest.fixture(autouse=True)
def deny_public_network(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    original_connect: Callable[..., Any] = socket.socket.connect
    original_getaddrinfo: Callable[..., Any] = socket.getaddrinfo

    def guarded_connect(instance: socket.socket, address: object) -> Any:
        if not isinstance(address, tuple) or not address or not _is_loopback_host(address[0]):
            raise OSError("PUBLIC_NETWORK_DISABLED")
        return original_connect(instance, address)

    def guarded_getaddrinfo(host: object, *args: object, **kwargs: object) -> Any:
        if not _is_loopback_host(host):
            raise OSError("PUBLIC_NETWORK_DISABLED")
        return original_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    yield
