import logging

from api.ApiAccessors import DataApiAccessor
from api.parsers.MapParser import MapParser
from api.parsers.MapPoolAssignmentParser import MapPoolAssignmentParser
from api.parsers.ModParser import ModParser
from client.connection import Dispatcher

logger = logging.getLogger(__name__)


class ModApiConnector(DataApiAccessor):
    def __init__(self, dispatch: Dispatcher) -> None:
        super().__init__('/data/mod')
        self.dispatch = dispatch

    def requestData(self, params: dict | None = None) -> None:
        params = params or {}
        self._add_default_include(params)
        self._extend_filters(params)
        self.get_by_query(params, self.handle_data)

    def _add_default_include(self, params: dict) -> dict:
        params["include"] = ",".join(("latestVersion", "reviewsSummary", "uploader"))
        return params

    def _extend_filters(self, params: dict) -> dict:
        additional_filter = "latestVersion.hidden=='false'"
        if cur_filters := params.get("filter", ""):
            params["filter"] = f"{cur_filters};{additional_filter}"
        else:
            params["filter"] = additional_filter
        return params

    def handle_data(self, message: dict) -> None:
        parsed_data = {
            "command": "modvault_info",
            "values":  ModParser.parse_many(message["data"]),
            "meta": message["meta"],
        }
        self.dispatch.dispatch(parsed_data)


class MapApiConnector(DataApiAccessor):
    def __init__(self, dispatch: Dispatcher) -> None:
        super().__init__("/data/map")
        self.dispatch = dispatch

    def requestData(self, params: dict | None = None) -> None:
        params = params or {}
        self._add_default_include(params)
        self._extend_filters(params)
        self.get_by_query(params, self.parse_data)

    def _extend_filters(self, params: dict) -> dict:
        additional_filter = "latestVersion.hidden=='false'"
        if cur_filters := params.get("filter", ""):
            params["filter"] = f"{cur_filters};{additional_filter}"
        else:
            params["filter"] = additional_filter
        return params

    def _add_default_include(self, params: dict) -> dict:
        params["include"] = ",".join(("latestVersion", "reviewsSummary", "author"))
        return params

    def parse_data(self, message: dict) -> None:
        prepared_data = {
            "command": "mapvault_info",
            "values": MapParser.parse_many(message["data"]),
            "meta": message["meta"],
        }
        self.dispatch.dispatch(prepared_data)


class MapPoolApiConnector(DataApiAccessor):
    def __init__(self, dispatch: Dispatcher) -> None:
        super().__init__('/data/mapPoolAssignment')
        self.dispatch = dispatch

    def requestData(self, params: dict | None) -> None:
        params = params or {}
        self.get_by_query(self._add_default_include(params), self.parse_data)

    def _add_default_include(self, params: dict) -> dict:
        params["include"] = ",".join((
            "mapVersion",
            "mapVersion.map",
            "mapVersion.map.author",
            "mapVersion.map.reviewsSummary",
        ))
        return params

    def parse_data(self, message: dict) -> None:
        prepared_data = {
            "command": "mapvault_info",
            "values": MapPoolAssignmentParser.parse_many_to_maps(message["data"]),
            "meta": message["meta"],
        }
        self.dispatch.dispatch(prepared_data)
