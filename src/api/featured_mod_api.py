import logging

from api.ApiAccessors import DataApiAccessor

logger = logging.getLogger(__name__)


class FeaturedModApiConnector(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__('/data/featuredMod')

    def prepare_data(self, message: dict) -> None:
        values = []
        for mod in message["data"]:
            prepared_mod = {
                "name": mod["technicalName"],
                "fullname": mod["displayName"],
                "publish": mod.get("visible", False),
                "order": mod.get("order", 0),
                "desc": mod.get(
                    "description",
                    "<i>No description provided</i>",
                ),
            }
            values.append(prepared_mod)
        return {"values": values}
