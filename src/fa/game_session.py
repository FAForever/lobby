import logging
from enum import IntEnum

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtCore import QObject
from PyQt6.QtCore import pyqtSignal

from src import client
from src.config import setup_file_handler
from src.connectivity.IceAdapterClient import IceAdapterClient
from src.connectivity.IceAdapterProcess import IceAdapterProcess
from src.connectivity.IceServersPoller import IceServersPoller
from src.fa.game_process import instance as game_process_instance

logger = logging.getLogger(__name__)
# Log to a separate file to not pollute normal log with huge json dumps
logger.propagate = False
logger.addHandler(setup_file_handler('gamesession.log'))


class GameSessionState(IntEnum):
    # Game services are entirely off
    OFF = 0
    # We're listening on the game port
    LISTENING = 1
    # We've verified our connectivity and are idle
    IDLE = 2
    # Game has been launched but we're not connected yet
    LAUNCHED = 3
    # Game is running and we're relaying gpgnet commands
    RUNNING = 4


class GameSession(QObject):
    ready = pyqtSignal()
    gameFullSignal = pyqtSignal()

    def __init__(self, player_id, player_login):
        QObject.__init__(self)
        self._state = GameSessionState.OFF
        self._rehost = False
        self.game_uid = None
        self.game_name = None
        self.game_mod = None
        self.game_visibility = None
        self.game_map = None
        self.game_password = None
        self.player_id = player_id
        self.player_login = player_login
        client.instance.lobby_dispatch.subscribe_to(
            'game', self.handle_message,
        )

        self._joins, self._connects = [], []

        self._process = game_process_instance  # type - GameProcess
        self._process.started.connect(self._launched)
        self._process.finished.connect(self._exited)

        self.state = GameSessionState.LISTENING

        self._relay_port = 0

        self.ice_adapter_process = None
        self.ice_adapter_client = None
        self.ice_servers_poller = None

    def startIceAdapter(self):
        self.ice_adapter_process = IceAdapterProcess(
            player_id=self.player_id,
            player_login=self.player_login,
            game_id=self.game_uid,
        )
        self.ice_adapter_client = IceAdapterClient(game_session=self)
        self.ice_adapter_client.statusChanged.connect(self.onIceAdapterStarted)
        self.ice_adapter_client.connect_(
            "127.0.0.1", self.ice_adapter_process.rpc_port(),
        )
        while self._relay_port == 0:
            QCoreApplication.processEvents()

    def onIceAdapterStarted(self, status: dict) -> None:
        self._relay_port = status["gpgnet"]["local_port"]
        logger.info(
            "ICE adapter started an listening on port {} for GPGNet "
            "connections".format(self._relay_port),
        )
        self.ice_adapter_client.statusChanged.disconnect(self.onIceAdapterStarted)
        self.ice_servers_poller = IceServersPoller(self.ice_adapter_client, self.game_uid)

    def closeIceAdapter(self):
        if self.ice_adapter_client:
            try:
                self.ice_adapter_client.call("quit", blocking=True)
            except RuntimeError:
                pass
            self.ice_adapter_client.close()
            self.ice_adapter_client = None
        if self.ice_adapter_process:
            self.ice_adapter_process.close()
            self.ice_adapter_process = None
        self._relay_port = 0

    @property
    def relay_port(self):
        return self._relay_port

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, val):
        self._state = val

    def handle_message(self, message):
        command, args = message.get('command'), message.get('args', [])
        if command == 'SendNatPacket':
            # we ignore that for now with the ICE Adapter
            pass
        elif command == 'CreatePermission':
            # we ignore that for now with the ICE Adapter
            pass
        elif command == 'JoinGame':
            login, peer_id = args
            self.ice_adapter_client.call("joinGame", [login, peer_id])
        elif command == 'HostGame':
            self.ice_adapter_client.call("hostGame", [args[0]])
        elif command == 'ConnectToPeer':
            login, peer_id, offer = args
            self.ice_adapter_client.call(
                "connectToPeer", [login, peer_id, offer],
            )
        elif command == 'DisconnectFromPeer':
            self.ice_adapter_client.call("disconnectFromPeer", [args[0]])
        elif command == "IceMsg":
            peer_id, ice_msg = args
            self.ice_adapter_client.call("iceMsg", [peer_id, ice_msg])
        else:
            logger.warning(
                "sending unhandled GPGNet message {} {}".format(command, args),
            )
            self.ice_adapter_client.call("sendToGpgNet", [command, args])

    def send(self, command_id, args):
        logger.info("Outgoing relay message {} {}".format(command_id, args))
        client.instance.lobby_connection.send({
            'command': command_id,
            'target': 'game',
            'args': args or [],
        })

    def setLobbyInitMode(self, lobby_init_mode):
        # to do: make this call synchronous/blocking, because init_mode must be
        # set before game_launch.
        # See ClientWindow.handle_game_launch()
        if (
            not self.ice_adapter_client
            or not self.ice_adapter_client.connected
        ):
            logger.error(
                "ICE adapter client not connected when calling "
                "setLobbyInitMode",
            )
            return
        self.ice_adapter_client.call("setLobbyInitMode", [lobby_init_mode])

    def _new_game_connection(self):
        logger.info("Game connected through GPGNet")
        self.state = GameSessionState.RUNNING
        self.ready.emit()

    def _on_game_message(self, command, args):
        logger.info("Incoming GPGNet: {} {}".format(command, args))
        if command == 'Rehost':
            self._rehost = True
        elif command == 'GameFull':
            self.gameFullSignal.emit()
        self.send(command, args)

    def _launched(self):
        logger.info("Game has started")
        client.instance.lobby_reconnector.keepalive = True

    def _exited(self, status):
        self.state = GameSessionState.OFF
        logger.info("Game has exited with status code: {}".format(status))
        self.send('GameState', ['Ended'])
        client.instance.lobby_reconnector.keepalive = False

        if self._rehost:
            client.instance.host_game(
                title=self.game_name,
                mod=self.game_mod,
                visibility=self.game_visibility,
                mapname=self.game_map,
                password=self.game_password,
                is_rehost=True,
            )

        self._rehost = False
        self.game_uid = None
        self.game_name = None
        self.game_mod = None
        self.game_visibility = None
        self.game_map = None
        self.game_password = None
        self.closeIceAdapter()
