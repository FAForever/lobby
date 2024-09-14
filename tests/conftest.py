import pytest

from src.model.game import Game
from src.model.gameset import Gameset
from src.model.player import Player
from src.model.playerset import Playerset


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
