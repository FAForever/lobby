import logging

from api.ApiAccessors import DataApiAccessor

logger = logging.getLogger(__name__)


class SimModFiles(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__('/data/modVersion')
        self.simModUrl = ''

    def requestData(self, queryDict: dict) -> None:
        self.get_by_query(queryDict, self.handleData)

    def getUrlFromMessage(self, message):
        self.simModUrl = message[0]['downloadUrl']

    def requestAndGetSimModUrlByUid(self, uid: int) -> str:
        queryDict = dict(filter='uid=={}'.format(uid))
        self.get_by_query(queryDict, self.getUrlFromMessage)
        self.waitForCompletion()
        return self.simModUrl
