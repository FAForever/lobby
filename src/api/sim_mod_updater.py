import logging

from src.api.ApiAccessors import DataApiAccessor

logger = logging.getLogger(__name__)


class SimModFiles(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__('/data/modVersion')
        self.mod_url = ""

    def get_url_from_message(self, message: dict) -> str:
        self.mod_url = message["data"][0]["downloadUrl"]

    def request_and_get_sim_mod_url_by_id(self, uid: str) -> str:
        query_dict = {"filter": f"uid=={uid}"}
        self.get_by_query(query_dict, self.get_url_from_message)
        self.waitForCompletion()
        return self.mod_url
