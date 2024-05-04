import logging

from api.ApiAccessors import DataApiAccessor
from api.models.FeaturedMod import FeaturedMod
from api.models.FeaturedModFile import FeaturedModFile
from api.parsers.FeaturedModFileParser import FeaturedModFileParser
from api.parsers.FeaturedModParser import FeaturedModParser

logger = logging.getLogger(__name__)


class FeaturedModApiConnector(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__("/data/featuredMod")

    def prepare_data(self, message: dict) -> dict[str, list[FeaturedMod]]:
        return {"values": FeaturedModParser.parse_many(message["data"])}

    def handle_featured_mod(self, message: dict) -> None:
        self.featured_mod = FeaturedModParser.parse(message["data"][0])

    def request_fmod_by_name(self, technical_name: str) -> None:
        queryDict = {"filter": f"technicalName=={technical_name}"}
        self.get_by_query(queryDict, self.handle_featured_mod)

    def request_and_get_fmod_by_name(self, technicalName) -> FeaturedMod:
        self.request_fmod_by_name(technicalName)
        self.waitForCompletion()
        return self.featured_mod


class FeaturedModFilesApiConnector(DataApiAccessor):
    def __init__(self, mod_id: str, version: str) -> None:
        super().__init__(f"/featuredMods/{mod_id}/files/{version}")
        self.featured_mod_files = []

    def handle_response(self, message: dict) -> None:
        self.featured_mod_files = FeaturedModFileParser.parse_many(message["data"])

    def get_files(self) -> list[FeaturedModFile]:
        self.requestData()
        self.waitForCompletion()
        return self.featured_mod_files
