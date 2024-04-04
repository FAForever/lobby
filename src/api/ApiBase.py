import json
import logging
from typing import Any
from typing import Callable

from PyQt6 import QtWidgets
from PyQt6.QtCore import QByteArray
from PyQt6.QtCore import QEventLoop
from PyQt6.QtCore import QObject
from PyQt6.QtCore import QUrl
from PyQt6.QtCore import QUrlQuery
from PyQt6.QtNetwork import QNetworkAccessManager
from PyQt6.QtNetwork import QNetworkReply
from PyQt6.QtNetwork import QNetworkRequest

from config import Settings
from oauth.oauth_flow import OAuth2Flow

logger = logging.getLogger(__name__)

DO_NOT_ENCODE = QByteArray()
DO_NOT_ENCODE.append(b":/?&=.,")


class ApiBase(QObject):
    oauth: OAuth2Flow = OAuth2Flow()

    def __init__(self, route: str = "") -> None:
        QObject.__init__(self)
        self.route = route
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.onRequestFinished)
        self._running = False
        self.handlers: dict[QNetworkReply | None, Callable[[dict], Any]] = {}

    @classmethod
    def set_oauth(cls, oauth: OAuth2Flow) -> None:
        cls.oauth = oauth

    def build_query_url(self, query_dict: dict) -> QUrl:
        query = QUrlQuery()
        for key, value in query_dict.items():
            query.addQueryItem(key, str(value))
        stringQuery = query.toString(QUrl.ComponentFormattingOption.FullyDecoded)
        percentEncodedByteArrayQuery = QUrl.toPercentEncoding(
            stringQuery,
            exclude=DO_NOT_ENCODE,
        )
        percentEncodedStrQuery = percentEncodedByteArrayQuery.data().decode()
        url = url = QUrl(Settings.get('api') + self.route)
        url.setQuery(percentEncodedStrQuery)
        return url

    @staticmethod
    def prepare_request(url: QUrl | None) -> QNetworkRequest:
        request = QNetworkRequest(url) if url else QNetworkRequest()
        # last 2 args are unused, but for some reason they are required
        ApiBase.oauth.prepareRequest(request, QByteArray(), QByteArray())
        # FIXME: remove when https://bugreports.qt.io/browse/QTBUG-123891 is deployed
        request.setAttribute(QNetworkRequest.Attribute.Http2AllowedAttribute, False)
        return request

    def get(self, url: QUrl, response_handler: Callable[[dict], Any]) -> None:
        self._running = True
        logger.debug("Sending API request with URL: {}".format(url.toString()))
        reply = self.manager.get(self.prepare_request(url))
        self.handlers[reply] = response_handler

    def onRequestFinished(self, reply: QNetworkReply) -> None:
        self._running = False
        if reply.error() != QNetworkReply.NetworkError.NoError:
            logger.error("API request error: {}".format(reply.error()))
        else:
            message_bytes = reply.readAll().data()
            message = json.loads(message_bytes.decode('utf-8'))
            included = self.parseIncluded(message)
            result = {}
            result["data"] = self.parseData(message, included)
            result["meta"] = self.parseMeta(message)
            self.handlers[reply](result)
        self.handlers.pop(reply)
        reply.deleteLater()

    def parseIncluded(self, message):
        result = {}
        relationships = []
        if "included" in message:
            for inc_item in message["included"]:
                if not inc_item["type"] in result:
                    result[inc_item["type"]] = {}
                if "attributes" in inc_item:
                    type_ = inc_item["type"]
                    id_ = inc_item["id"]
                    result[type_][id_] = inc_item["attributes"]
                if "relationships" in inc_item:
                    for key, value in inc_item["relationships"].items():
                        relationships.append((
                            inc_item["type"], inc_item["id"], key, value,
                        ))
            message.pop('included')
        # resolve relationships
        for r in relationships:
            result[r[0]][r[1]][r[2]] = self.parseData(r[3], result)
        return result

    def parseData(self, message, included):
        if "data" in message:
            if isinstance(message["data"], (list)):
                result = []
                for data in message["data"]:
                    result.append(self.parseSingleData(data, included))
                return result
            elif isinstance(message["data"], (dict)):
                return self.parseSingleData(message["data"], included)
        else:
            logger.error("error in response", message)
        if "included" in message:
            logger.error("unexpected 'included' in message", message)
        return {}

    def parseSingleData(self, data, included):
        result = {}
        try:
            if (
                data["type"] in included
                and data["id"] in included[data["type"]]
            ):
                result = included[data["type"]][data["id"]]
            result["id"] = data["id"]
            if "type" not in result:
                result["type"] = data["type"]
            if "attributes" in data:
                for key, value in data["attributes"].items():
                    result[key] = value
            if "relationships" in data:
                for key, value in data["relationships"].items():
                    result[key] = self.parseData(value, included)
        except BaseException:
            logger.error("error parsing ", data)
        return result

    def parseMeta(self, message):
        if "meta" in message:
            return message["meta"]
        return {}

    def waitForCompletion(self):
        waitFlag = QEventLoop.ProcessEventsFlag.WaitForMoreEvents
        while self._running:
            QtWidgets.QApplication.processEvents(waitFlag)
