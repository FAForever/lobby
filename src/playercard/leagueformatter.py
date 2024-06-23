import os

from PyQt6.QtGui import QImage
from PyQt6.QtGui import QPixmap

import util
from api.models.LeaderboardRating import LeaderboardRating
from api.models.LeagueSeasonScore import LeagueSeasonScore
from api.stats_api import LeagueSeasonScoreApiConnector
from downloadManager import Downloader
from downloadManager import DownloadRequest

FormClass, BaseClass = util.THEME.loadUiType("player_card/playerleague.ui")


class LegueFormatter(FormClass, BaseClass):
    def __init__(
            self,
            player_id: str,
            rating: LeaderboardRating,
            league_score_api: LeagueSeasonScoreApiConnector,
    ) -> None:
        BaseClass.__init__(self)
        self.setupUi(self)
        self.load_stylesheet()

        self.divisionLabel.setText("Unlisted")
        icon = util.THEME.pixmap("player_card/unlisted.png")
        self.iconLabel.setPixmap(icon.scaled(80, 80))

        self.gamesLabel.setText(f"{rating.total_games:.0f} Games")
        # chr(0xB1) = +-
        rating_str = f"{rating.rating:.0f} [{rating.mean:.0f}\xb1{rating.deviation:.0f}]"
        self.ratingLabel.setText(rating_str)

        assert rating.leaderboard is not None

        self.leaderboardLabel.setText(rating.leaderboard.pretty_name)
        self.league_score_api = league_score_api
        self.league_score_api.score_ready.connect(self.on_league_score_ready)

        self.leaderboard = rating.leaderboard
        self.league_score_api.get_player_score_in_leaderboard(
            player_id, self.leaderboard.technical_name,
        )

        self.leaderboardLabel.setText(self.leaderboard.pretty_name)

        self._downloader = Downloader(os.path.join(util.CACHE_DIR, "divisions"))
        self._images_dl_request = DownloadRequest()
        self._images_dl_request.done.connect(self.on_image_downloaded)

    def load_stylesheet(self) -> None:
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

    def on_league_score_ready(self, score: LeagueSeasonScore) -> None:
        if score.season.leaderboard.technical_name != self.leaderboard.technical_name:
            return

        if score.score is None:
            self.divisionLabel.setText("Unlisted")
            return

        subdivision = score.subdivision
        league_name = f"{subdivision.division.name} {subdivision.name}"
        self.divisionLabel.setText(league_name)

        image_name = os.path.basename(subdivision.image_url)
        image_path = os.path.join(util.CACHE_DIR, "divisions", image_name)
        if os.path.isfile(image_path):
            self.set_league_icon(image_path)
        else:
            self.download_league_icon(subdivision.image_url)

    def set_league_icon(self, image_path: str) -> None:
        image = QImage(image_path)
        self.iconLabel.setPixmap(QPixmap(image).scaled(160, 80))

    def download_league_icon(self, url: str) -> None:
        name = os.path.basename(url)
        self._downloader.download(name, self._images_dl_request, url)

    def on_image_downloaded(self, _: str, result: tuple[str, bool]) -> None:
        image_path, download_failed = result
        if not download_failed:
            self.set_league_icon(image_path)
