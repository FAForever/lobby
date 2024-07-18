from __future__ import annotations

import time
from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Any
from typing import Callable
from typing import Iterable

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets
from PyQt6.QtCore import QModelIndex
from PyQt6.QtCore import QObject
from PyQt6.QtCore import QRect
from PyQt6.QtCore import QSize
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QPainter
from PyQt6.QtGui import QPen
from PyQt6.QtWidgets import QHBoxLayout
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QLayout
from PyQt6.QtWidgets import QListView
from PyQt6.QtWidgets import QStyle
from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtWidgets import QStyleOptionViewItem
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget

import util
from config import Settings
from downloadManager import DownloadRequest
from fa import maps
from games.moditem import mods
from model.rating import Rating
from util.qt import qpainter
from util.qt_list_model import QtListModel


class GameResult(Enum):
    WIN = "Win"
    LOSE = "Lose"
    PLAYING = "Playing"
    UNKNOWN = "???"


class ScoreboardModelItem(QObject):
    updated = pyqtSignal()

    def __init__(self, player: dict, mod: str | None) -> None:
        QObject.__init__(self)
        self.player = player
        self.mod = mod or ""

        if len(self.player["ratingChanges"]) > 0:
            self.rating_stats = self.player["ratingChanges"][0]
        else:
            self.rating_stats = None

    @classmethod
    def builder(cls, mod: str | None) -> Callable[[dict], ScoreboardModelItem]:
        def build(data: dict) -> ScoreboardModelItem:
            return cls(data, mod)
        return build

    def score(self) -> int:
        return self.player["score"]

    def login(self) -> str:
        return self.player["player"]["login"]

    def rating_before(self) -> int:
        # gamePlayerStats' fields 'before*' and 'after*' can be removed
        # at any time and 'ratingChanges' can be absent if game result is
        # undefined
        if self.rating_stats is not None:
            rating = Rating(
                self.rating_stats["meanBefore"],
                self.rating_stats["deviationBefore"],
            )
            return round(rating.displayed())
        elif self.player.get("beforeMean") and self.player.get("beforeDeviation"):
            rating = Rating(
                self.player["beforeMean"],
                self.player["beforeDeviation"],
            )
            return round(rating.displayed())
        return 0

    def rating_after(self) -> int:
        if self.rating_stats is not None:
            rating = Rating(
                self.rating_stats["meanAfter"],
                self.rating_stats["deviationAfter"],
            )
            return round(rating.displayed())
        elif self.player.get("afterMean") and self.player.get("afterDeviation"):
            rating = Rating(
                self.player["afterMean"],
                self.player["afterDeviation"],
            )
            return round(rating.displayed())
        return 0

    def rating(self) -> int | None:
        if self.rating_stats is None and "beforeMean" not in self.player:
            return None
        return self.rating_before()

    def rating_change(self) -> int:
        if self.rating_stats is None:
            return 0
        return self.rating_after() - self.rating_before()

    def faction_name(self) -> str:
        if "faction" in self.player:
            if self.player["faction"] == 1:
                faction = "UEF"
            elif self.player["faction"] == 2:
                faction = "Aeon"
            elif self.player["faction"] == 3:
                faction = "Cybran"
            elif self.player["faction"] == 4:
                faction = "Seraphim"
            elif self.player["faction"] == 5:
                if self.mod == "nomads":
                    faction = "Nomads"
                else:
                    faction = "Random"
            elif self.player["faction"] == 6:
                if self.mod == "nomads":
                    faction = "Random"
                else:
                    faction = "broken"
            else:
                faction = "broken"
        else:
            faction = "Missing"
        return faction

    def icon(self) -> QIcon:
        return util.THEME.icon(f"replays/{self.faction_name()}.png")


class ScoreboardModel(QtListModel):
    def __init__(
            self,
            spoiled: bool,
            alignment: Qt.AlignmentFlag,
            item_builder: Callable[[Any], QObject],
    ) -> None:
        QtListModel.__init__(self, item_builder)
        self.spoiled = spoiled
        self.alignment = alignment

    def get_alignment(self) -> Qt.AlignmentFlag:
        return self.alignment

    def add_player(self, player: dict) -> None:
        self._add_item(player, player["player"]["id"])


class ScoreboardItemDelegate(QStyledItemDelegate):
    def __init__(self) -> None:
        QStyledItemDelegate.__init__(self)
        self._row_height = 22

    def row_height(self) -> int:
        return self._row_height

    def sizeHint(self, option, index) -> QSize:
        size = QStyledItemDelegate.sizeHint(self, option, index)
        return QSize(size.width(), self._row_height)

    def _draw_score(
            self,
            painter: QPainter,
            rect: QRect,
            player_data: ScoreboardModelItem,
            alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
    ) -> QRect:
        score = f"{player_data.score()}"
        score_rect = QRect(rect)
        score_rect.setWidth(20)
        if alignment == Qt.AlignmentFlag.AlignRight:
            score_rect.moveLeft(rect.width() - score_rect.width())
        painter.drawText(score_rect, Qt.AlignmentFlag.AlignCenter, score)
        return score_rect

    def _draw_icon(
            self,
            painter: QPainter,
            rect: QRect,
            player_data: ScoreboardModelItem,
            alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
    ) -> QRect:
        icon = player_data.icon()
        icon_rect = QRect(rect)
        icon_rect.setWidth(40)
        icon_rect.setHeight(20)
        if alignment == Qt.AlignmentFlag.AlignRight:
            icon_rect.moveLeft(rect.width() - icon_rect.width())
        icon.paint(painter, icon_rect)
        return icon_rect

    def _draw_nick_and_rating(
        self,
        painter: QPainter,
        rect: QRect,
        player_data: ScoreboardModelItem,
        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
    ) -> QRect:
        rating = player_data.rating()
        rating_str = f"{rating}" if rating is not None else "???"
        text = self._get_elided_text(painter, f"{player_data.login()} ({rating_str})", rect.width())
        painter.drawText(rect, alignment, text)
        return rect

    def _draw_rating_change(
        self,
        painter: QPainter,
        rect: QRect,
        player_data: ScoreboardModelItem,
        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
    ) -> QRect:
        change = player_data.rating_change()
        rating_change_rect = QRect(rect)
        rating_change_rect.setWidth(30)
        if alignment == Qt.AlignmentFlag.AlignRight:
            rating_change_rect.moveLeft(rect.width() - rating_change_rect.width())
        color = painter.pen().color()
        if change > 0:
            color = Qt.GlobalColor.green
        elif change < 0:
            color = Qt.GlobalColor.red
        with qpainter(painter):
            painter.setPen(QPen(color))
            painter.drawText(rating_change_rect, Qt.AlignmentFlag.AlignCenter, f"{change:+}")
        return rating_change_rect

    def _draw_clear_option(self, painter: QPainter, option: QStyleOptionViewItem) -> None:
        option.text = ""
        control_element = QStyle.ControlElement.CE_ItemViewItem
        option.widget.style().drawControl(control_element, option, painter, option.widget)

    def _shrink_rect_along(
            self,
            rect: QRect,
            adjustment: int,
            alignment: Qt.AlignmentFlag,
    ) -> QRect:
        """
        Returns a new rect shrinked from left or right side
        by given adjustment
        """
        direction = 1 if alignment == Qt.AlignmentFlag.AlignLeft else -1
        index = 0 if alignment == Qt.AlignmentFlag.AlignLeft else 2
        adjustments = [0, 0, 0, 0]
        adjustments[index] = adjustment * direction
        return rect.adjusted(*adjustments)

    def _get_elided_text(self, painter: QPainter, text: str, width: int) -> str:
        metrics = painter.fontMetrics()
        return metrics.elidedText(text, Qt.TextElideMode.ElideRight, width)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        player_data: ScoreboardModelItem = index.data()
        team_model: ScoreboardModel = index.model()
        team_alignment = team_model.get_alignment()
        rect = QRect(option.rect)

        with qpainter(painter):
            self._draw_clear_option(painter, option)

            if team_model.spoiled:
                score_rect = self._draw_score(painter, rect, player_data, team_alignment)
                rect = self._shrink_rect_along(rect, score_rect.width(), team_alignment)

                diff_rect = self._draw_rating_change(painter, rect, player_data, team_alignment)
                rect = self._shrink_rect_along(rect, diff_rect.width(), team_alignment)

            icon_rect = self._draw_icon(painter, rect, player_data, team_alignment)
            rect = self._shrink_rect_along(rect, icon_rect.width() + 3, team_alignment)

            self._draw_nick_and_rating(painter, rect, player_data, team_alignment)


class Scoreboard(QWidget):
    GAME_RESULT_RESERVED_HEIGHT = 30
    TITLE_RESERVED_HEIGHT = 30

    def __init__(
            self,
            mod: str | None,
            winner: dict | None,
            spoiled: bool,
            duration: str | None,
            teamwin: dict | None,
            uid: str,
            teams: dict,
    ) -> None:
        super().__init__()
        self.winner = winner
        self.spoiled = spoiled
        self.duration = duration or ""
        self.teamwin = teamwin
        self.uid = uid
        self.teams = teams
        self.num_teams = len(self.teams)
        self.biggest_team = max(len(team) for team in self.teams.values()) if self.teams else 0

        self.main_layout = QVBoxLayout()
        if self.num_teams == 2:
            self.teams_layout = QHBoxLayout()
        else:
            self.teams_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.mod = mod
        self._height = 0
        self._team_heights = []

    def create_teamlist_view(self) -> QListView:
        team_view = QListView()
        team_view.setObjectName("replayScoreTeamList")
        return team_view

    def _create_team_result_label(self, text: str) -> QLabel:
        result_label = QLabel(text)
        result_label.setObjectName("replayGameResult")
        result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font = result_label.font()
        font.setPointSize(font.pointSize() + 4)
        result_label.setFont(font)

        return result_label

    def add_result_label(self, text: str, layout: QLayout) -> None:
        result_label = self._create_team_result_label(text)
        layout.addWidget(result_label)

    def teamview_rows(self, view: QListView) -> int:
        model: ScoreboardModel = view.model()
        if self.num_teams == 2:
            return self.biggest_team
        return model.rowCount(QModelIndex())

    def teamview_height(self, view: QListView) -> int:
        row_count = self.teamview_rows(view)
        delegate: ScoreboardItemDelegate = view.itemDelegate()
        return row_count * delegate.row_height()

    def adjust_teamview_height(self, view: QListView, height: int) -> None:
        view.setMinimumHeight(height)
        view.setMaximumHeight(height)

    def add_team_score(
            self,
            alignment: Qt.AlignmentFlag,
            team_result: GameResult,
            players: Iterable[dict],
    ) -> None:
        team_layout = QVBoxLayout()
        self.add_result_label(team_result.value, team_layout)

        model = ScoreboardModel(self.spoiled, alignment, ScoreboardModelItem.builder(self.mod))
        for player in players:
            model.add_player(player)

        team_view = self.create_teamlist_view()
        team_view.setModel(model)
        team_view.setItemDelegate(ScoreboardItemDelegate())
        team_layout.addWidget(team_view)

        view_height = self.teamview_height(team_view)
        self.adjust_teamview_height(team_view, view_height)
        self._team_heights.append(self.GAME_RESULT_RESERVED_HEIGHT + view_height)

        self.teams_layout.addLayout(team_layout)

    def add_team_score_if_needed(
            self,
            alignment: Qt.AlignmentFlag,
            team_result: GameResult,
            players: Iterable[dict],
    ) -> None:
        if len(list(players)) == 0:
            return
        self.add_team_score(alignment, team_result, players)

    def height(self) -> int:
        # there must be a way to dissect all of the layouts and widgets
        # with all of their paddings, spacings, margins etc. to determine
        # scoreboard's precise height, but this works good enough
        magic = 40
        if len(self.teams) == 2:
            return self._height + max(self._team_heights) + magic
        return sum((self._height, *self._team_heights, magic))

    def width(self) -> int:
        if len(self.teams) == 2:
            return 560 if self.spoiled else 500
        return 335 if self.spoiled else 275

    def one_team_layout(self) -> None:
        team = list(self.teams.values())[0]
        alignment = Qt.AlignmentFlag.AlignLeft
        if self.spoiled:
            winners, losers = [], []
            for player in team:
                if self.winner is not None and player["score"] == self.winner["score"]:
                    winners.append(player)
                else:
                    losers.append(player)
            self.add_team_score_if_needed(alignment, self.game_result(is_winner=True), winners)
            self.add_team_score_if_needed(alignment, self.game_result(is_winner=False), losers)
        else:
            self.add_team_score_if_needed(alignment, self.game_result(is_winner=False), team)
        self.main_layout.addLayout(self.teams_layout)

    def default_layout(self) -> None:
        alignment = Qt.AlignmentFlag.AlignLeft
        for team in self.teams:
            game_result = self.game_result(is_winner=(team == self.teamwin))
            self.add_team_score(alignment, game_result, self.teams[team])
        self.main_layout.addLayout(self.teams_layout)

    def game_result(self, *, is_winner: bool) -> GameResult:
        if not self.spoiled:
            return GameResult.UNKNOWN
        if "playing" in self.duration:
            return GameResult.PLAYING
        return (GameResult.LOSE, GameResult.WIN)[is_winner]

    def two_teams_layout(self) -> None:
        for index, team_num in enumerate(self.teams):
            alignment = (Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignRight)[index]
            is_winner = team_num == self.teamwin
            game_result = self.game_result(is_winner=is_winner)
            self.add_team_score(alignment, game_result, self.teams[team_num])
            if index == 0:
                self.add_vs_label()
        self.main_layout.addLayout(self.teams_layout)

    def create_title_label(self) -> QLabel:
        title_label = QLabel(f"Replay UID: {self.uid}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        title_font = title_label.font()
        title_font.setPointSize(title_font.pointSize() + 4)
        title_font.setBold(True)
        title_label.setFont(title_font)

        return title_label

    def add_title_label(self) -> None:
        self.main_layout.addWidget(self.create_title_label())
        self._height += self.TITLE_RESERVED_HEIGHT

    def create_vs_label(self) -> QLabel:
        vs_label = QLabel("VS")
        vs_label.setObjectName("VSLabel")
        vs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font = vs_label.font()
        font.setPointSize(font.pointSize() + 13)
        vs_label.setFont(font)

        return vs_label

    def add_vs_label(self) -> None:
        self.teams_layout.addWidget(self.create_vs_label())

    def setup(self) -> None:
        self.add_title_label()

        if self.num_teams == 1:
            self.one_team_layout()
        elif self.num_teams == 2:
            self.two_teams_layout()
        else:
            self.default_layout()


class ReplayItemDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, *args, **kwargs):
        QtWidgets.QStyledItemDelegate.__init__(self, *args, **kwargs)

    def paint(self, painter, option, index, *args, **kwargs):
        self.initStyleOption(option, index)

        painter.save()

        html = QtGui.QTextDocument()
        html.setHtml(option.text)

        icon = QtGui.QIcon(option.icon)
        iconsize = icon.actualSize(option.rect.size())

        # clear icon and text before letting the control draw itself because
        # we're rendering these parts ourselves
        option.icon = QtGui.QIcon()
        option.text = ""
        option.widget.style().drawControl(
            QtWidgets.QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget,
        )

        # Shadow
        # painter.fillRect(option.rect.left()+8-1, option.rect.top()+8-1,
        #                  iconsize.width(), iconsize.height(),
        #                  QtGui.QColor("#202020"))

        # Icon
        icon.paint(
            painter, option.rect.adjusted(3, -2, 0, 0),
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter,
        )

        # Frame around the icon
        # pen = QtWidgets.QPen()
        # pen.setWidth(1)
        # FIXME: This needs to come from theme.
        # pen.setBrush(QtGui.QColor("#303030"))

        # pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        # painter.setPen(pen)
        # painter.drawRect(option.rect.left()+5-2, option.rect.top()+5-2,
        #                  iconsize.width(), iconsize.height())

        # Description
        painter.translate(
            option.rect.left() + iconsize.width() + 10,
            option.rect.top() + 10,
        )
        clip = QtCore.QRectF(
            0, 0, option.rect.width() - iconsize.width() - 15,
            option.rect.height(),
        )
        html.drawContents(painter, clip)

        painter.restore()

    def sizeHint(self, option, index, *args, **kwargs):
        clip = index.model().data(index, QtCore.Qt.ItemDataRole.UserRole)
        self.initStyleOption(option, index)
        html = QtGui.QTextDocument()
        html.setHtml(option.text)
        html.setTextWidth(240)
        if clip:
            return QtCore.QSize(215, clip.height)
        else:
            return QtCore.QSize(215, 35)


class ReplayItem(QtWidgets.QTreeWidgetItem):
    # list element
    FORMATTER_REPLAY = str(
        util.THEME.readfile(
            "replays/formatters/replay.qthtml",
        ),
    )
    # replay-info elements
    FORMATTER_REPLAY_INFORMATION = (
        "<h2 align='center'>Replay UID : {uid}</h2><table border='0' "
        "cellpadding='0' cellspacing='5' align='center'><tbody>{teams}</tbody>"
        "</table>"
    )
    FORMATTER_REPLAY_TEAM_SPOILED = (
        "<tr><td colspan='3' align='center' valign='middle'><font size='+2'>"
        "{title}</font></td></tr>{players}"
    )
    FORMATTER_REPLAY_FFA_SPOILED = (
        "<tr><td colspan='3' align='center' valign='middle'><font size='+2'>"
        "Win</font></td></tr>{winner}<tr><td colspan=3 align='center' "
        "valign='middle'><font size='+2'>Lose</font></td></tr>{players}"
    )
    FORMATTER_REPLAY_TEAM2_SPOILED = (
        "<td><table border=0><tr><td colspan='3' align='center' "
        "valign='middle'><font size='+2'>{title}</font></td></tr>{players}"
        "</table></td>"
    )
    FORMATTER_REPLAY_TEAM2 = "<td><table border=0>{players}</table></td>"
    FORMATTER_REPLAY_PLAYER_SCORE = (
        "<td align='center' valign='middle' width='20'>{player_score}</td>"
    )
    FORMATTER_REPLAY_PLAYER_ICON = (
        "<td width='40'><img src='{faction_icon_uri}' width='40' height='20'>"
        "</td>"
    )
    FORMATTER_REPLAY_PLAYER_LABEL = (
        "<td align='{alignment}' valign='middle' width='130'>{player_name} "
        "({player_rating})</td>"
    )

    def __init__(self, uid, parent, *args, **kwargs):
        QtWidgets.QTreeWidgetItem.__init__(self, *args, **kwargs)

        self.uid = uid
        self.parent = parent
        self.height = 70
        self.viewtext = None
        self.viewtextPlayer = None
        self.mapname = None
        self.mapdisplayname = None
        self.client = None
        self.title = None
        self.host = None

        self.startDate = None
        self.duration = None
        self.live_delay = False

        self.extra_info_loaded = False
        self.spoiled = False
        self.url = "{}/{}".format(Settings.get('replay_vault/host'), self.uid)

        self.teams = {}
        self.access = None
        self.mod = None
        self.moddisplayname = None

        self.options = []
        self.players = []
        self.numberplayers = 0
        self.biggestTeam = 0
        self.winner = None
        self.teamWin = None

        self.setHidden(True)
        self.extraInfoWidth = 0  # panel with more information
        self.extraInfoHeight = 0  # panel with more information

        self._map_dl_request = DownloadRequest()
        self._map_dl_request.done.connect(self._on_map_preview_downloaded)

    def update(self, replay, client):
        """ Updates this item from the message dictionary supplied """
        self.replay = replay

        self.client = client
        self.name = replay["name"]

        if "id" in replay["mapVersion"]:
            self.mapid = replay["mapVersion"]["id"]
            self.mapname = replay["mapVersion"]["folderName"]
            self.previewUrlLarge = replay["mapVersion"]["thumbnailUrlLarge"]
        else:
            self.mapname = "unknown"

        startDt = datetime.strptime(replay["startTime"], '%Y-%m-%dT%H:%M:%SZ')
        # local time
        startDt = startDt.replace(tzinfo=timezone.utc).astimezone(tz=None)

        if replay["endTime"] is None:
            seconds = time.time() - startDt.timestamp()
            if seconds > 86400:  # more than 24 hours
                self.duration = (
                    "<font color='darkgrey'>end time<br />&nbsp;missing</font>"
                )
            elif seconds > 7200:  # more than 2 hours
                self.duration = (
                    time.strftime('%H:%M:%S', time.gmtime(seconds))
                    + "<br />?playing?"
                )
            elif seconds < 300:  # less than 5 minutes
                self.duration = (
                    time.strftime('%H:%M:%S', time.gmtime(seconds))
                    + "<br />&nbsp;<font color='darkred'>playing</font>"
                )
                self.live_delay = True
            else:
                self.duration = (
                    time.strftime('%H:%M:%S', time.gmtime(seconds))
                    + "<br />&nbsp;playing"
                )
        else:
            endDt = datetime.strptime(replay["endTime"], '%Y-%m-%dT%H:%M:%SZ')
            # local time
            endDt = endDt.replace(tzinfo=timezone.utc).astimezone(tz=None)
            self.duration = time.strftime(
                '%H:%M:%S',
                time.gmtime((endDt - startDt).total_seconds()),
            )

        self.startHour = startDt.strftime("%H:%M")
        self.startDate = startDt.strftime("%Y-%m-%d")

        self.modid = replay["featuredMod"]["id"]
        self.mod = replay["featuredMod"]["technicalName"]

        # Map preview code
        self.mapdisplayname = maps.getDisplayName(self.mapname)

        self.icon = maps.preview(self.mapname)
        if not self.icon:
            self.icon = util.THEME.icon("games/unknown_map.png")
            if self.mapname != "unknown":
                self.client.map_preview_downloader.download_preview(
                    self.mapname, self._map_dl_request,
                )

        if self.mod in mods:
            self.moddisplayname = mods[self.mod].name
        else:
            self.moddisplayname = self.mod

        self.viewtext = self.FORMATTER_REPLAY.format(
            time=self.startHour, name=self.name, map=self.mapdisplayname,
            duration=self.duration, mod=self.moddisplayname,
        )

    def _on_map_preview_downloaded(self, mapname, result):
        path, is_local = result
        self.icon = util.THEME.icon(path, is_local)
        self.setIcon(0, self.icon)

    def load_extra_info(self) -> None:
        """
        processes information from the server about a replay into readable
        extra information for the user, also calls method to show the
        information
        """

        self.extra_info_loaded = True
        playersList = self.replay['playerStats']
        self.numberplayers = len(playersList)

        mvpscore = 0
        mvp = None
        scores = {}

        for player in playersList:  # player highscore
            if "score" in player:
                if player["score"] > mvpscore:
                    mvp = player
                    mvpscore = player["score"]

        # player -> teams & playerscore -> teamscore
        for player in playersList:
            # get ffa like into one team
            if self.mod == "phantomx" or self.mod == "murderparty":
                team = 1
            else:
                team = int(player["team"])

            if team == -1:
                continue

            if "score" in player:
                if team in scores:
                    scores[team] = scores[team] + player["score"]
                else:
                    scores[team] = player["score"]
            if team not in self.teams:
                self.teams[team] = [player]
            else:
                self.teams[team].append(player)

        if self.numberplayers == len(self.teams):  # some kind of FFA
            self.teams = {}
            scores = {}
            team = 1
            for player in playersList:  # player -> team (1)
                if team not in self.teams:
                    self.teams[team] = [player]
                else:
                    self.teams[team].append(player)

        if len(self.teams) == 1 or len(self.teams) == len(playersList):
            self.winner = mvp
        elif len(scores) > 0:  # team highscore
            mvt = 0
            for team in scores:
                if scores[team] > mvt:
                    self.teamWin = team
                    mvt = scores[team]

    def generate_scoreboard(self) -> Scoreboard:
        if not self.extra_info_loaded:
            self.load_extra_info()
        self.spoiled = not self.parent.spoilerCheckbox.isChecked()
        scoreboard = Scoreboard(
            self.mod, self.winner, self.spoiled,
            self.duration, self.teamWin, self.uid, self.teams,
        )
        scoreboard.setup()
        return scoreboard

    def pressed(self) -> None:
        menu = QtWidgets.QMenu(self.parent)
        actionDownload = QAction("Download replay", menu)
        actionDownload.triggered.connect(self.downloadReplay)
        menu.addAction(actionDownload)
        menu.popup(QtGui.QCursor.pos())

    def downloadReplay(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.url))

    def display(self, column):
        if column == 0:
            return self.viewtext
        if column == 1:
            return self.viewtext

    def data(self, column, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.display(column)
        elif role == QtCore.Qt.ItemDataRole.UserRole:
            return self
        return super(ReplayItem, self).data(column, role)

    def permutations(self, items):
        """  Yields all permutations of the items. """
        if items == []:
            yield []
        else:
            for i in range(len(items)):
                for j in self.permutations(items[:i] + items[i + 1:]):
                    yield [items[i]] + j

    def __ge__(self, other):
        """  Comparison operator used for item list sorting """
        return not self.__lt__(other)

    def __lt__(self, other):
        """ Comparison operator used for item list sorting """
        if not self.client:
            return True  # If not initialized...
        if not other.client:
            return False
        # Default: uid
        return self.uid < other.uid
