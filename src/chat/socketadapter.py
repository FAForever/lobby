from __future__ import annotations

import logging
import time

from irc.client import Reactor
from PyQt6.QtCore import QEventLoop
from PyQt6.QtCore import QObject
from PyQt6.QtCore import QUrl
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtNetwork import QAbstractSocket
from PyQt6.QtNetwork import QNetworkRequest
from PyQt6.QtWebSockets import QWebSocket

logger = logging.getLogger(__name__)


class WebSocketToSocket(QObject):
    """ Allows to use QWebSocket as a 'socket' """

    message_received = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.socket = QWebSocket()
        self.socket.binaryFrameReceived.connect(self.on_bin_message_received)
        self.socket.textMessageReceived.connect(self.on_text_message_received)
        self.socket.errorOccurred.connect(self.on_socket_error)
        self.buffer = b""

    def on_socket_error(self, error: QAbstractSocket.SocketError) -> None:
        logger.error(f"SocketAdapter error: {error}. Details: {self.socket.errorString()}")

    def on_bin_message_received(self, message: bytes) -> None:
        # according to https://ircv3.net/specs/extensions/websocket
        # messages MUST NOT include trailing \r\n, but our non-websocket
        # library (irc) requires them
        self.buffer += message + b"\r\n"
        self.message_received.emit()

    def on_text_message_received(self, message: str) -> None:
        self.buffer += f"{message}\r\n".encode()
        self.message_received.emit()

    def read(self, size: int) -> bytes:
        ans, self.buffer = self.buffer[:size], self.buffer[size:]
        return ans

    def recv(self, size: int) -> bytes:
        """ Alias for read, just in case """
        return self.read(size)

    def shutdown(self, how: int) -> None:
        self.socket.deleteLater()

    def write(self, message: bytes) -> None:
        self.socket.sendBinaryMessage(message.strip())

    def send(self, message: bytes) -> None:
        """ Alias for write, just in case """
        self.write(message)

    def _prepare_request(self, server_address: tuple[str, int]) -> QNetworkRequest:
        host, port = server_address
        request = QNetworkRequest()
        request.setUrl(QUrl(f"wss://{host}:{port}"))
        request.setRawHeader(b"Sec-WebSocket-Protocol", b"binary.ircv3.net")
        return request

    def connect(self, server_address: tuple[str, int]) -> None:
        self.socket.open(self._prepare_request(server_address))

        # FIXME: maybe there are too many usages of this loop trick
        loop = QEventLoop()
        self.socket.connected.connect(loop.exit)
        loop.exec()

    def close(self) -> None:
        self.socket.close()


class ReactorForSocketAdapter(Reactor):
    def process_once(self, timeout: float = 0.01) -> None:
        if self.sockets:
            self.process_data(self.sockets)
        else:
            time.sleep(timeout)
        self.process_timeout()


class ConnectionFactory:
    def connect(self, server_address: tuple[str, int]) -> None:
        sock = WebSocketToSocket()
        sock.connect(server_address)
        return sock

    __call__ = connect
