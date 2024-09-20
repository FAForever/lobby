import os

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap

from src import util
from src.api.models.LeaderboardRating import LeaderboardRating
from src.api.models.LeagueSeasonScore import LeagueSeasonScore
from src.api.stats_api import LeagueSeasonScoreApiConnector
from src.downloadManager import DownloadRequest
from src.downloadManager import ImageDownloader

FormClass, BaseClass = util.THEME.loadUiType("player_card/playerleague.ui")


class LeagueFormatter(FormClass, BaseClass):
    def __init__(
            self,
            player_id: str,
            rating: LeaderboardRating,
            league_score_api: LeagueSeasonScoreApiConnector,
    ) -> None:
        BaseClass.__init__(self)
        self.setupUi(self)
        self.load_stylesheet()

        self.rating = rating
        self.leaderboard = rating.leaderboard
        self.player_id = player_id

        self.league_score_api = league_score_api
        self.league_score_api.score_ready.connect(self.on_league_score_ready)

        self._downloader = ImageDownloader(util.DIVISIONS_CACHE_DIR, QSize(160, 80))
        self._images_dl_request = DownloadRequest()
        self._images_dl_request.done.connect(self.on_image_downloaded)

        self.fill_ui()
        self.fetch_league_score()

    def load_stylesheet(self) -> None:
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

    def default_pixmap(self) -> QPixmap:
        return util.THEME.pixmap("player_card/unlisted.png").scaled(80, 80)

    def default_league(self) -> str:
        return "Unlisted"

    def rating_text(self) -> str:
        # chr(0xB1) = +-
        return f"{self.rating.rating:.0f} [{self.rating.mean:.0f}\xb1{self.rating.deviation:.0f}]"

    def fill_ui(self) -> None:
        self.divisionLabel.setText(self.default_league())
        self.set_league_icon(self.default_pixmap())
        self.gamesLabel.setText(f"{self.rating.total_games:.0f} Games")
        self.ratingLabel.setText(self.rating_text())
        self.leaderboardLabel.setText(self.leaderboard.pretty_name)

    def fetch_league_score(self) -> None:
        self.league_score_api.get_player_score_in_leaderboard(
            self.player_id, self.leaderboard.technical_name,
        )

    def on_league_score_ready(self, score: LeagueSeasonScore) -> None:
        if score.season.leaderboard.technical_name != self.leaderboard.technical_name:
            return

        if score.score is None:
            return

        subdivision = score.subdivision
        league_name = f"{subdivision.division.name} {subdivision.name}"
        self.divisionLabel.setText(league_name)

        image_name = os.path.basename(subdivision.image_url)
        self.set_league_icon(self.icon(image_name))
        self.download_league_icon_if_needed(subdivision.image_url)

    def icon(self, image_name: str = "") -> QPixmap:
        if (pixmap := self._downloader.get_image(image_name)) is not None:
            return pixmap
        return self.default_pixmap()

    def set_league_icon(self, pixmap: QPixmap) -> None:
        self.iconLabel.setPixmap(pixmap)

    def download_league_icon_if_needed(self, url: str) -> None:
        self._downloader.download_if_needed(url, self._images_dl_request)

    def on_image_downloaded(self, _: str, pixmap: QPixmap) -> None:
        self.set_league_icon(pixmap)


class GlobalLeagueFormatter(LeagueFormatter):
    def default_pixmap(self) -> QPixmap:
        return util.THEME.pixmap("player_card/global.png").scaled(80, 80)

    def default_league(self) -> str:
        return ""

    def fetch_league_score(self) -> None:
        return


def league_formatter_factory(
        player_id: str,
        rating: LeaderboardRating,
        api: LeagueSeasonScoreApiConnector,
) -> LeagueFormatter | GlobalLeagueFormatter:
    if rating.leaderboard.technical_name == "global":
        return GlobalLeagueFormatter(player_id, rating, api)
    return LeagueFormatter(player_id, rating, api)
