from PyQt6.QtCore import QDateTime
from PyQt6.QtCore import QObject
from PyQt6.QtCore import QTimer
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtNetwork import QNetworkAccessManager
from PyQt6.QtNetworkAuth import QOAuth2AuthorizationCodeFlow
from PyQt6.QtNetworkAuth import QOAuthHttpServerReplyHandler

from config import Settings
from decorators import with_logger


class OAuthReplyHandler(QOAuthHttpServerReplyHandler):
    def callback(self) -> str:
        with_trailing_slash = super().callback()
        # remove trailing slash because server does not accept it
        return with_trailing_slash.removesuffix("/")


@with_logger
class OAuth2Flow(QOAuth2AuthorizationCodeFlow):
    def __init__(
            self,
            manager: QNetworkAccessManager | None = None,
            parent: QObject | None = None,
    ) -> None:
        super().__init__(manager, parent)

        if manager is None:
            self.setNetworkAccessManager(QNetworkAccessManager())

        self.setup_credentials()
        reply_handler = OAuthReplyHandler(self)
        self.setReplyHandler(reply_handler)

        self.authorizeWithBrowser.connect(QDesktopServices.openUrl)
        self.requestFailed.connect(self.on_request_failed)
        self.granted.connect(self.on_granted)
        self.tokenChanged.connect(self.on_token_changed)
        self.expirationAtChanged.connect(self.on_expiration_at_changed)

        self._check_timer = QTimer(self)
        self._check_timer.timeout.connect(self.check_token)
        self._check_interval = 5000
        self._expires_in = None

    def stop_checking_expiration(self) -> None:
        self._check_timer.stop()
        self._expires_in = None

    def start_checking_expiration(self) -> None:
        self._check_timer.start(self._check_interval)

    def check_token(self) -> None:
        if self._expires_in is None:
            return

        self._expires_in -= self._check_interval
        if self._expires_in <= 60_000:
            self.refreshAccessToken()

    def on_expiration_at_changed(self, expiration_at: QDateTime) -> None:
        self._logger.debug(f"Token expiration at changed to: {expiration_at}")
        self._expires_in = QDateTime.currentDateTime().msecsTo(expiration_at)

    def on_token_changed(self, new_token: str) -> None:
        self._logger.debug(f"Token changed to: {new_token}")

    def on_granted(self) -> None:
        self._logger.debug("Token granted successfuly!")
        self.start_checking_expiration()

    def on_request_failed(self, error: QOAuth2AuthorizationCodeFlow.Error) -> None:
        self._logger.debug(f"Request failed with an error: {error}")
        self.stop_checking_expiration()

    def setup_credentials(self) -> None:
        """
        Set client's credentials, scopes and OAuth endpoints
        """
        # client_id = Settings.get("oauth/client_id")
        client_id = "faf-java-client"  # FIXME: ask to configure ports for python client
        scopes = Settings.get("oauth/scope")

        oauth_host = QUrl(Settings.get("oauth/host"))
        auth_endpoint = QUrl(Settings.get("oauth/auth_endpoint"))
        token_endpoint = QUrl(Settings.get("oauth/token_endpoint"))

        authorization_url = oauth_host.resolved(auth_endpoint)
        token_url = oauth_host.resolved(token_endpoint)

        self.setUserAgent("FAF Client")
        self.setAuthorizationUrl(authorization_url)
        self.setClientIdentifier(client_id)
        self.setAccessTokenUrl(token_url)
        self.setScope(" ".join(scopes))
