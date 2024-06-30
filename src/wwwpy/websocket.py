from __future__ import annotations

from enum import Enum
from typing import NamedTuple, Callable

from wwwpy.common.typing import Protocol


class WebsocketRoute(NamedTuple):
    path: str
    on_connect: Callable[[WebsocketEndpoint], None]


class PoolChange(Enum):
    add = 'add'
    remove = 'remove'


class PoolChangeCallback(Protocol):
    def __call__(self, change: PoolChange, endpoint: WebsocketEndpoint, pool: WebsocketPool) -> None: ...


def _noop(change: PoolChange, endpoint: WebsocketEndpoint, pool: WebsocketPool):
    pass


class WebsocketPool:

    def __init__(self, route: str, before_change: PoolChangeCallback = None):
        if before_change is None:
            before_change = _noop
        self._before_change: PoolChangeCallback = before_change
        self.clients: list[WebsocketEndpoint] = []
        self.http_route = WebsocketRoute(route, self._on_connect)

    def _on_connect(self, endpoint: WebsocketEndpoint) -> None:

        self._before_change(PoolChange.add, endpoint, self)

        def handle_remove(msg: str | bytes | None):
            if msg is None:
                self._before_change(PoolChange.remove, endpoint, self)
                self.clients.remove(endpoint)

        endpoint.listeners.append(handle_remove)
        self.clients.append(endpoint)


class ListenerProtocol(Protocol):
    def __call__(self, message: str | bytes | None) -> None: ...

class WebsocketEndpoint:
    def __init__(self, send: ListenerProtocol):
        """The send argument is called by the IO implementation: it will deliver outgoing messages"""
        self._send = send
        self.listeners: list[ListenerProtocol] = []

    # part to be called by user code to send a outgoing message
    def send(self, message: str | bytes | None) -> None:
        self._send(message)

    # parte to be used by IO implementation to be called to notify incoming messages
    def on_message(self, message: str | bytes | None) -> None:
        for listener in self.listeners:
            listener(message)

