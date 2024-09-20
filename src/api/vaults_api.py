import logging
from collections.abc import Sequence

from src.api.ApiAccessors import DataApiAccessor
from src.api.parsers.MapParser import MapParser
from src.api.parsers.MapPoolAssignmentParser import MapPoolAssignmentParser
from src.api.parsers.ModParser import ModParser

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
        self.get_by_query(query, self.handle_response)

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


class ModApiConnector(VaultsApiConnector):
    def __init__(self) -> None:
        super().__init__("/data/mod")

    def _extend_query_options(self, query_options: dict) -> dict:
        super()._extend_query_options(query_options)
        self._extend_includes(query_options, ["uploader"])
        return query_options

    def prepare_data(self, message: dict) -> dict:
        return {
            "values": ModParser.parse_many(message["data"]),
            "meta": message["meta"],
        }


class MapApiConnector(VaultsApiConnector):
    def __init__(self) -> None:
        super().__init__("/data/map")

    def _extend_query_options(self, query_options: dict) -> None:
        super()._extend_query_options(query_options)
        self._extend_includes(query_options, ["author"])

    def prepare_data(self, message: dict) -> dict:
        return {
            "values": MapParser.parse_many(message["data"]),
            "meta": message["meta"],
        }


class MapPoolApiConnector(VaultsApiConnector):
    def __init__(self) -> None:
        super().__init__("/data/mapPoolAssignment")
        self._includes = (
            "mapVersion",
            "mapVersion.map",
            "mapVersion.map.author",
            "mapVersion.map.reviewsSummary",
        )

    def _extend_query_options(self, query_options: dict) -> dict:
        self._add_default_includes(query_options)
        return query_options

    def prepare_data(self, message: dict) -> dict:
        return {
            "values": MapPoolAssignmentParser.parse_many_to_maps(message["data"]),
            "meta": message["meta"],
        }
