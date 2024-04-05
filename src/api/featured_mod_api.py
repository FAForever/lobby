import logging

from api.ApiAccessors import DataApiAccessor
from client.connection import Dispatcher

logger = logging.getLogger(__name__)


class FeaturedModApiConnector(DataApiAccessor):
    def __init__(self, dispatch: Dispatcher) -> None:
        super().__init__('/data/featuredMod')
        self.dispatch = dispatch

    def requestData(self) -> None:
        self.get_by_query({}, self.handleData)

    def handleData(self, message: dict) -> None:
        preparedData = {
            "command": "mod_info_api",
            "values": [],
        }
        for mod in message["data"]:
            preparedMod = {
                "command": "mod_info_api",
                "name": mod["technicalName"],
                "fullname": mod["displayName"],
                "publish": mod.get("visible", False),
                "order": mod.get("order", 0),
                "desc": mod.get(
                    "description",
                    "<i>No description provided</i>",
                ),
            }
            preparedData["values"].append(preparedMod)
        self.dispatch.dispatch(preparedData)
