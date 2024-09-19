import pytest

from src.model.game import Game
from src.model.gameset import Gameset
from src.model.player import Player
from src.model.playerset import Playerset


@pytest.fixture(scope="module")
def application(qapp, request):
    return qapp


@pytest.fixture(scope="function")
def signal_receiver(application):
    from PyQt6 import QtCore

    class SignalReceiver(QtCore.QObject):
        def __init__(self, parent=None):
            QtCore.QObject.__init__(self, parent)
            self.int_values = []
            self.generic_values = []
            self.string_values = []

        @QtCore.pyqtSlot()
        def generic_slot(self):
            self.generic_values.append(None)

        @QtCore.pyqtSlot(str)
        def string_slot(self, value):
            self.string_values.append(value)

        @QtCore.pyqtSlot(int)
        def int_slot(self, value):
            self.int_values.append(value)

    return SignalReceiver(application)


@pytest.fixture
def client_instance():
    from src.client import instance
    return instance


@pytest.fixture
def player(mocker):
    return mocker.MagicMock(spec=Player)


@pytest.fixture
def game(mocker):
    return mocker.MagicMock(spec=Game)


@pytest.fixture
def playerset(mocker):
    return mocker.MagicMock(spec=Playerset)


@pytest.fixture
def gameset(mocker):
    return mocker.MagicMock(spec=Gameset)


@pytest.fixture
def mouse_position(client_instance):
    from src.client.mouse_position import MousePosition
    return MousePosition(client_instance)
