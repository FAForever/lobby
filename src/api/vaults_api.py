import logging
from collections.abc import Sequence

from api.ApiAccessors import DataApiAccessor
from api.parsers.MapParser import MapParser
from api.parsers.MapPoolAssignmentParser import MapPoolAssignmentParser
from api.parsers.ModParser import ModParser
from client.connection import Dispatcher

logger = logging.getLogger(__name__)


class VaultsApiConnector(DataApiAccessor):
    def __init__(self, route: str) -> None:
        super().__init__(route)
        self._includes = ("latestVersion", "reviewsSummary")

    def _extend_query_options(self, query_options: dict) -> dict:
        self._add_default_includes(query_options)
        self._apply_default_filters(query_options)
        return query_options

    def _copy_query_options(self, query_options: dict | None) -> dict:
        query_options = query_options or {}
        return query_options.copy()

    def request_data(self, query_options: dict | None = None) -> None:
        query = self._copy_query_options(query_options)
        self._extend_query_options(query)
        self.get_by_query(query, self.parse_data)

    def _add_default_includes(self, query_options: dict) -> dict:
        return self._extend_includes(query_options, self._includes)

    def _extend_includes(self, query_options: dict, to_include: Sequence[str]) -> dict:
        cur_includes = query_options.get("include", "")
        to_include_str = ",".join((cur_includes, *to_include)).removeprefix(",")
        query_options["include"] = to_include_str
        return query_options

    def _apply_default_filters(self, query_options: dict) -> dict:
        cur_filters = query_options.get("filter", "")
        additional_filter = "latestVersion.hidden=='false'"
        query_options["filter"] = ";".join((cur_filters, additional_filter)).removeprefix(";")
        return query_options

    def parse_data(self, message: dict) -> None:
        raise NotImplementedError


class ModApiConnector(VaultsApiConnector):
    def __init__(self, dispatch: Dispatcher) -> None:
        super().__init__("/data/mod")
        self.dispatch = dispatch

    def _extend_query_options(self, query_options: dict) -> dict:
        super()._extend_query_options(query_options)
        self._extend_includes(query_options, ["uploader"])
        return query_options

    def parse_data(self, message: dict) -> None:
        parsed_data = {
            "command": "modvault_info",
            "values":  ModParser.parse_many(message["data"]),
            "meta": message["meta"],
        }
        self.dispatch.dispatch(parsed_data)


class MapApiConnector(VaultsApiConnector):
    def __init__(self, dispatch: Dispatcher) -> None:
        super().__init__("/data/map")
        self.dispatch = dispatch

    def _extend_query_options(self, query_options: dict) -> dict:
        super()._extend_query_options(query_options)
        self._extend_includes(query_options, ["author"])

    def parse_data(self, message: dict) -> None:
        prepared_data = {
            "command": "mapvault_info",
            "values": MapParser.parse_many(message["data"]),
            "meta": message["meta"],
        }
        self.dispatch.dispatch(prepared_data)


class MapPoolApiConnector(VaultsApiConnector):
    def __init__(self, dispatch: Dispatcher) -> None:
        super().__init__("/data/mapPoolAssignment")
        self.dispatch = dispatch
        self._includes = (
            "mapVersion",
            "mapVersion.map",
            "mapVersion.map.author",
            "mapVersion.map.reviewsSummary",
        )

    def _extend_query_options(self, query_options: dict) -> dict:
        self._add_default_includes(query_options)
        return query_options

    def parse_data(self, message: dict) -> None:
        prepared_data = {
            "command": "mapvault_info",
            "values": MapPoolAssignmentParser.parse_many_to_maps(message["data"]),
            "meta": message["meta"],
        }
        self.dispatch.dispatch(prepared_data)
