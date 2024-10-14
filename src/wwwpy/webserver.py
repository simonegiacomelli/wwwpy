from __future__ import annotations

from abc import ABC, abstractmethod
from time import sleep

from wwwpy.http import HttpRoute
from wwwpy.server.wait_url import wait_url
from wwwpy.websocket import WebsocketRoute


class Webserver(ABC):
    def __init__(self) -> None:
        self.host: str = '0.0.0.0'
        self.port: int = 7777

    def set_host(self, host: str) -> 'Webserver':
        self.host = host
        return self

    def set_port(self, port: int) -> 'Webserver':
        self.port = port
        return self

    def start_listen(self) -> 'Webserver':
        device_ip = f' - http://{_get_ip()}:{self.port}\n' if self.host == '0.0.0.0' else ''
        print(f'Starting web server on:\n'
              f' - http://{self.host}:{self.port}\n'
              f' - {self.localhost_url()}\n' +
              device_ip
              )
        self._start_listen()
        self.wait_ready()
        return self

    def set_http_route(self, *http_routes: HttpRoute | WebsocketRoute) -> 'Webserver':
        for http_route in http_routes:
            self._setup_route(http_route)
        return self

    @abstractmethod
    def _setup_route(self, route: HttpRoute | WebsocketRoute) -> None:
        pass

    @abstractmethod
    def _start_listen(self) -> None:
        pass

    def wait_ready(self) -> 'Webserver':
        wait_url(self.localhost_url() + '/check_if_webserver_is_accepting_requests')
        return self

    def localhost_url(self) -> str:
        return f'http://127.0.0.1:{self.port}'


def wait_forever() -> None:
    while True:
        sleep(10)


def _get_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP