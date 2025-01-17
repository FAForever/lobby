from __future__ import annotations

import json
import logging
import os
import time

from PyQt6 import QtCore
from PyQt6 import QtNetwork
from PyQt6 import QtWidgets

from src import fa
from src import util
from src.config import Settings

GPGNET_HOST = "lobby.faforever.com"
GPGNET_PORT = 8000

DEFAULT_LIVE_REPLAY = True


class ReplayRecorder(QtCore.QObject):
    """
    This is a simple class that takes all the FA replay data input from
    its inputSocket, writes it to a file, and relays it to an internet
    server via its relaySocket.
    """
    __logger = logging.getLogger(__name__)

    def __init__(
            self,
            parent: ReplayServer,
            local_socket: QtNetwork.QTcpSocket,
            *args,
            **kwargs,
    ) -> None:
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.parent = parent
        self.inputSocket = local_socket
        self.inputSocket.setSocketOption(QtNetwork.QTcpSocket.SocketOption.KeepAliveOption, 1)
        self.inputSocket.readyRead.connect(self.readDatas)
        self.inputSocket.disconnected.connect(self.inputDisconnected)
        self.__logger.info("FA connected locally.")

        # Create a file to write the replay data into
        self.replayData = QtCore.QByteArray()
        self.replayInfo = fa.instance._info

        self._host = Settings.get('replay_server/host')
        self._port = Settings.get('replay_server/port', type=int)
        # Open the relay socket to our server
        self.relaySocket = QtNetwork.QTcpSocket(self.parent)
        self.relaySocket.connectToHost(self._host, self._port)

        if util.settings.value(
            "fa.live_replay", DEFAULT_LIVE_REPLAY, type=bool,
        ):
            # Maybe make this asynchronous
            if self.relaySocket.waitForConnected(1000):
                self.__logger.debug(
                    "internet replay server {}:{}".format(
                        self.relaySocket.peerName(),
                        self.relaySocket.peerPort(),
                    ),
                )
            else:
                self.__logger.error("no connection to internet replay server")

    def __del__(self):
        # Clean up our socket objects, in accordance to the hint from the Qt
        # docs (recommended practice)
        self.__logger.debug("destructor entered")
        self.inputSocket.deleteLater()
        self.relaySocket.deleteLater()

    def readDatas(self):
        # CAVEAT: readAll() was seemingly truncating data here
        read = self.inputSocket.read(self.inputSocket.bytesAvailable())

        if not isinstance(read, bytes):
            self.__logger.warning(
                "Read failure on inputSocket: {}".format(bytes.decode()),
            )
            return

        # Convert data into a bytearray for easier processing
        data = QtCore.QByteArray(read)

        # Record locally
        if self.replayData.isEmpty():
            # This prefix means "P"osting replay in the livereplay protocol of
            # FA, this needs to be stripped from the local file
            if data.startsWith(b"P/"):
                rest = data.indexOf(b"\x00") + 1
                self.__logger.info(
                    "Stripping prefix '{}' from replay."
                    .format(data.left(rest - 1)),
                )
                self.replayData.append(data.right(data.size() - rest))
            else:
                self.replayData.append(data)
        else:
            # Write to buffer
            self.replayData.append(data)

        # Relay to faforever.com
        if self.relaySocket.isOpen():
            self.relaySocket.write(data)

    def done(self):
        self.__logger.info("closing replay file")
        self.parent.removeRecorder(self)

    @QtCore.pyqtSlot()
    def inputDisconnected(self):
        self.__logger.info("FA disconnected locally.")

        # Part of the hardening - ensure all buffered local replay data is read
        # and relayed
        if self.inputSocket.bytesAvailable():
            self.__logger.info(
                "Relaying remaining bytes: {}"
                .format(self.inputSocket.bytesAvailable()),
            )
            self.readDatas()

        # Part of the hardening - ensure successful sending of the rest of the
        # replay to the server
        if self.relaySocket.bytesToWrite():
            self.__logger.info(
                "Waiting for replay transmission to finish: {} "
                "bytes".format(self.relaySocket.bytesToWrite()),
            )

            progress = QtWidgets.QProgressDialog(
                "Finishing Replay Transmission", "Cancel", 0, 0,
            )
            progress.show()

            while self.relaySocket.bytesToWrite() and progress.isVisible():
                QtWidgets.QApplication.processEvents()

            progress.close()

        self.relaySocket.disconnectFromHost()

        self.writeReplayFile()

        self.done()

    def writeReplayFile(self):
        # Update info block if possible.
        if (
            fa.instance._info
            and fa.instance._info['uid'] == self.replayInfo['uid']
        ):
            if fa.instance._info.setdefault('complete', False):
                self.__logger.info("Found Complete Replay Info")
            else:
                self.__logger.warning("Replay Info not Complete")

            self.replayInfo = fa.instance._info

        self.replayInfo['game_end'] = time.time()

        basename = "{}-{}.fafreplay".format(
            self.replayInfo['uid'], self.replayInfo['recorder'],
        )
        filename = os.path.join(util.REPLAY_DIR, basename)
        self.__logger.info(
            "Writing local replay as {}, containing {} bytes "
            "of replay data.".format(filename, self.replayData.size()),
        )

        replay = QtCore.QFile(filename)
        replay.open(QtCore.QIODevice.OpenModeFlag.WriteOnly | QtCore.QIODevice.OpenModeFlag.Text)
        replay.write(json.dumps(self.replayInfo).encode('utf-8'))
        replay.write(b'\n')
        replay.write(QtCore.qCompress(self.replayData).toBase64())
        replay.close()


class ReplayServer(QtNetwork.QTcpServer):
    """
    This is a local listening server that FA can send its replay data to.
    It will instantiate a fresh ReplayRecorder for each FA instance that
    launches.
    """
    __logger = logging.getLogger(__name__)

    def __init__(self, client, *args, **kwargs):
        QtNetwork.QTcpServer.__init__(self, *args, **kwargs)
        self.recorders = []
        self.client = client  # type - ClientWindow
        self.__logger.debug("initializing...")
        self.newConnection.connect(self.acceptConnection)

    def doListen(self) -> bool:
        while not self.isListening():
            self.listen(QtNetwork.QHostAddress.SpecialAddress.LocalHost, 0)
            if self.isListening():
                self.__logger.info(
                    "listening on address {}:{}".format(
                        self.serverAddress().toString(),
                        self.serverPort(),
                    ),
                )
            else:
                self.__logger.error(
                    "cannot listen, port probably used by "
                    "another application: {}".format(self.serverPort()),
                )
                answer = QtWidgets.QMessageBox.warning(
                    None,
                    "Port Occupied",
                    (
                        "FAF couldn't start its local replay server, which is "
                        "needed to play Forged Alliance online. Possible "
                        "reasons: <ul><li><b>FAF is already running</b> (most "
                        "likely)</li><li>another program is listening on port "
                        "{}</li></ul>".format(self.serverPort())
                    ),
                    QtWidgets.QMessageBox.StandardButton.Retry,
                    QtWidgets.QMessageBox.StandardButton.Abort,
                )
                if answer == QtWidgets.QMessageBox.StandardButton.Abort:
                    return False
        return True

    def removeRecorder(self, recorder):
        if recorder in self.recorders:
            self.recorders.remove(recorder)

    @QtCore.pyqtSlot()
    def acceptConnection(self):
        socket = self.nextPendingConnection()
        self.__logger.debug("incoming connection...")
        self.recorders.append(ReplayRecorder(self, socket))
