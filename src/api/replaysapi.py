import logging

from api.ApiAccessors import DataApiAccessor
from client.connection import Dispatcher

logger = logging.getLogger(__name__)


class ReplaysApiConnector(DataApiAccessor):
    def __init__(self, dispatch: Dispatcher) -> None:
        super().__init__('/data/game')
        self.dispatch = dispatch

    def requestData(self, params: dict) -> None:
        self.get_by_query(params, self.handleData)

    def handleData(self, message):
        preparedData = dict(
            command="replay_vault",
            action="search_result",
            replays={},
            featuredMods={},
            maps={},
            players={},
            playerStats={},
        )

        preparedData["replays"] = message["data"]

        self.dispatch.dispatch(preparedData)
