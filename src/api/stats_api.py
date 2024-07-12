import logging

from PyQt6.QtCore import QDateTime
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal

from api.ApiAccessors import DataApiAccessor
from api.models.Leaderboard import Leaderboard
from api.models.LeaderboardRatingJournal import LeaderboardRatingJournal
from api.models.LeagueSeasonScore import LeagueSeasonScore
from api.models.PlayerEvent import PlayerEvent
from api.parsers.LeaderboardParser import LeaderboardParser
from api.parsers.LeaderboardRatingJournalParser import LeaderboardRatingJournalParser
from api.parsers.LeaderboardRatingParser import LeaderboardRatingParser

logger = logging.getLogger(__name__)


class LeaderboardRatingApiConnector(DataApiAccessor):
    player_ratings_ready = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__('/data/leaderboardRating')

    def get_player_ratings(self, pid: str) -> None:
        query = {
            "include": "leaderboard",
            "filter": f"player.id=={pid}",
        }
        self.get_by_query(query, self.handle_player_ratings)

    def handle_player_ratings(self, message: dict) -> None:
        ratings = {"values": LeaderboardRatingParser.parse_many(message)}
        self.player_ratings_ready.emit(ratings)


class LeaderboardApiConnector(DataApiAccessor):
    def __init__(self) -> None:
        super().__init__("/data/leaderboard")

    def prepare_data(self, message: dict) -> dict[str, list[Leaderboard]]:
        return {"values": LeaderboardParser.parse_many(message)}


class LeaderboardRatingJournalApiConnector(DataApiAccessor):
    ratings_ready = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__("/data/leaderboardRatingJournal")
        self._result: list[LeaderboardRatingJournal] = []
        self.query = {}

    def handle_page(self, message: dict) -> None:
        total_pages = message["meta"]["page"]["totalPages"]
        current_page = message["meta"]["page"]["number"]
        self._result.extend(LeaderboardRatingJournalParser.parse_many(message))
        if current_page < total_pages:
            self.get_history_page(current_page + 1)
        else:
            self.ratings_ready.emit({"values": self._result})

    def get_history_page(self, page: int) -> None:
        self.query.update({
            "page[size]": 10000,
            "page[number]": page,
            "page[totals]": "",
        })
        self.get_by_query(self.query, self.handle_page)

    def get_full_history(self, pid: str, leaderboard: str) -> None:
        self._result.clear()
        self.query.update({
            "include": "gamePlayerStats,leaderboard",
            "filter": (
                f"gamePlayerStats.player.id=={pid!r};"
                f"leaderboard.technicalName=={leaderboard!r};"
                "gamePlayerStats.scoreTime=isnull='false'"
            ),
            "sort": "gamePlayerStats.scoreTime",
        })
        self.get_history_page(1)


class LeagueSeasonScoreApiConnector(DataApiAccessor):
    score_ready = pyqtSignal(LeagueSeasonScore)

    def __init__(self) -> None:
        super().__init__("/data/leagueSeasonScore")

    def prepare_data(self,  message: dict) -> dict[str, list[LeagueSeasonScore]]:
        return {"values": [LeagueSeasonScore(**entry) for entry in message["data"]]}

    def handle_score(self, message: dict) -> None:
        if message["data"]:
            self.score_ready.emit(LeagueSeasonScore(**message["data"][0]))

    def get_player_score_in_leaderboard(self, player_id: str, leaderboard: str) -> None:
        include = (
            "leagueSeasonDivisionSubdivision",
            "leagueSeasonDivisionSubdivision.leagueSeasonDivision",
            "leagueSeason",
            "leagueSeason.leaderboard",
        )
        utc_str = QDateTime.currentDateTime().toUTC().toString(Qt.DateFormat.ISODate)
        filters = (
            f"loginId=={player_id!r}",
            f"leagueSeason.leaderboard.technicalName=={leaderboard!r}",
            f"leagueSeason.startDate=le={utc_str}",
            f"leagueSeason.endDate=ge={utc_str}",
        )
        query_params = {"include": ",".join(include), "filter": ";".join(filters)}
        self.get_by_query(query_params, self.handle_score)


class PlayerEventApiAccessor(DataApiAccessor):
    events_ready = pyqtSignal(list)

    def __init__(self) -> None:
        super().__init__("/data/playerEvent")

    def get_player_events(self, player_id: str) -> None:
        query = {
            "include": "event",
            "filter": f"player.id=={player_id}",
        }
        self.get_by_query(query, self.handle_player_events)

    def handle_player_events(self, message: dict) -> None:
        self.events_ready.emit([PlayerEvent(**entry) for entry in message["data"]])
