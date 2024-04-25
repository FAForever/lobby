import logging

from api.ApiAccessors import DataApiAccessor

logger = logging.getLogger(__name__)


class FeaturedModFiles(DataApiAccessor):
    def __init__(self, mod_id: int, version: str) -> None:
        super().__init__('/featuredMods/{}/files/{}'.format(mod_id, version))
        self.featuredModFiles = []

    def handle_response(self, message):
        self.featuredModFiles = message["data"]

    def getFiles(self):
        self.requestData()
        self.waitForCompletion()
        return self.featuredModFiles


class FeaturedModId(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__('/data/featuredMod')
        self.featuredModId = 0

    def handleFeaturedModId(self, message):
        self.featuredModId = message['data'][0]['id']

    def requestFeaturedModIdByName(self, technicalName: str) -> None:
        queryDict = dict(filter='technicalName=={}'.format(technicalName))
        self.get_by_query(queryDict, self.handleFeaturedModId)

    def requestAndGetFeaturedModIdByName(self, technicalName):
        self.requestFeaturedModIdByName(technicalName)
        self.waitForCompletion()
        return self.featuredModId
