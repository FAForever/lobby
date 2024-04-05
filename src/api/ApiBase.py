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
        self.host_config_key = ""
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
        url = self._get_host_url().resolved(QUrl(self.route))
        url.setQuery(percentEncodedStrQuery)
        return url

    def _get_host_url(self) -> QUrl:
        return QUrl(Settings.get(self.host_config_key))

    # query arguments like filter=login==Rhyza
    def get_by_query(self, query_dict: dict, response_handler: Callable[[dict], Any]) -> None:
        url = self.build_query_url(query_dict)
        self.get(url, response_handler)

    def get_by_endpoint(self, endpoint: str, response_handler: Callable[[dict], Any]) -> None:
        url = self._get_host_url().resolved(QUrl(endpoint))
        self.get(url, response_handler)

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

    def parse_message(self, message: dict) -> dict:
        return message

    def onRequestFinished(self, reply: QNetworkReply) -> None:
        self._running = False
        if reply.error() != QNetworkReply.NetworkError.NoError:
            logger.error("API request error: {}".format(reply.error()))
        else:
            message_bytes = reply.readAll().data()
            message = json.loads(message_bytes.decode('utf-8'))
            result = self.parse_message(message)
            self.handlers[reply](result)
        self.handlers.pop(reply)
        reply.deleteLater()

    def waitForCompletion(self):
        waitFlag = QEventLoop.ProcessEventsFlag.WaitForMoreEvents
        while self._running:
            QtWidgets.QApplication.processEvents(waitFlag)
