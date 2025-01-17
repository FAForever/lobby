from __future__ import annotations

import os
from itertools import batched
from typing import Iterator
from typing import NamedTuple

from PyQt6.QtCore import QSize
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGridLayout
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QProgressBar
from PyQt6.QtWidgets import QSizePolicy
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget

from src.api.models.Achievement import Achievement
from src.api.models.Achievement import ProgressType
from src.api.models.Achievement import State
from src.api.models.PlayerAchievement import PlayerAchievement
from src.api.stats_api import AchievementsApiAccessor
from src.api.stats_api import PlayerAchievementApiAccessor
from src.downloadManager import DownloadRequest
from src.downloadManager import ImageDownloader
from src.util import ACHIEVEMENTS_CACHE_DIR
from src.util import THEME

FormClass, BaseClass = THEME.loadUiType("player_card/achievement.ui")


class AchievementWidget(FormClass, BaseClass):
    def __init__(self, player_achievement: PlayerAchievement, img_dler: ImageDownloader) -> None:
        BaseClass.__init__(self)
        self.setupUi(self)

        self.player_achievement = player_achievement
        self.achievement = player_achievement.achievement
        self.img_dler = img_dler
        self.img_dl_request = DownloadRequest()
        self.img_dl_request.done.connect(self.on_icon_downloaded)

    def setup(self) -> None:
        self.achievementNameLabel.setText(self.achievement.name)
        self.achievementDescLabel.setText(self.achievement.description)

        self.add_progress_if_present()

        self.detailsLayout.addRow(
            QLabel("Unlockers:"),
            QLabel(f"{self.achievement.unlockers_count} ({self.achievement.unlockers_percent}%)"),
        )
        self.detailsLayout.addRow(
            QLabel("Experience points"),
            QLabel(str(self.achievement.experience_points)),
        )

        self.add_achievement_image()

    def add_progress_if_present(self) -> None:
        if self.achievement.progress_type != ProgressType.INCREMENTAL:
            return

        bar = QProgressBar()
        bar.setObjectName("achievementBar")
        bar.setMaximum(self.achievement.total_steps)
        bar.setValue(self.player_achievement.current_steps)
        bar.setFormat("%v/%m")
        self.detailsLayout.addRow(bar)

    def add_achievement_image(self) -> None:
        image_name = os.path.basename(self.achievement.revealed_icon_url)
        self.set_icon(self.icon(image_name))
        self.download_icon_if_needed(self.achievement.revealed_icon_url)

    def icon(self, icon_name: str = "") -> QPixmap:
        if (pixmap := self.img_dler.get_image(icon_name)) is not None:
            return pixmap
        return THEME.pixmap("player_card/achievement.png")

    def set_icon(self, pixmap: QPixmap) -> None:
        self.iconLabel.setPixmap(pixmap)
        self.iconLabel.setEnabled(self.player_achievement.current_state == State.UNLOCKED)

    def on_icon_downloaded(self, _: str, pixmap: QPixmap) -> None:
        self.set_icon(pixmap)

    def download_icon_if_needed(self, url: str) -> None:
        self.img_dler.download_if_needed(url, self.img_dl_request)


class AchievementsHandler:
    def __init__(self, layout: QVBoxLayout, player_id: str) -> None:
        self.player_id = player_id
        self.layout = layout
        self.player_achievements_api = PlayerAchievementApiAccessor()
        self.player_achievements_api.achievments_ready.connect(self.on_player_achievements_ready)

        self.achievements_api = AchievementsApiAccessor()
        self.achievements_api.data_ready.connect(self.on_achievements_ready)
        self.img_dler = ImageDownloader(ACHIEVEMENTS_CACHE_DIR, QSize(128, 128))
        self.all_achievements = []
        self._loaded = False

    def run(self) -> None:
        if not self._loaded:
            self.achievements_api.requestData()

    def on_achievements_ready(self, achievements: dict[str, Iterator[Achievement]]) -> None:
        for achievement in achievements["values"]:
            self.all_achievements.append(achievement)
        self.player_achievements_api.get_achievements(self.player_id)

    def mock_player_achievement(self, achievement: Achievement) -> PlayerAchievement:
        return PlayerAchievement(
            id="0",
            create_time="",
            update_time="",
            current_steps=(None, 0)[achievement.progress_type == ProgressType.INCREMENTAL],
            state=State.REVEALED,
            achievement=achievement,
        )

    def create_group_title_label(self, text: str) -> QLabel:
        label = QLabel(text)
        font = label.font()
        font.setPointSize(font.pointSize() + 8)
        font.setBold(True)
        label.setFont(font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def create_hline(self) -> QWidget:
        hline = QWidget()
        hline.setObjectName("hline")
        hline.setFixedHeight(2)
        hline.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return hline

    def create_achievement_group_layout(self, group: list[PlayerAchievement]) -> QGridLayout:
        layout = QGridLayout()
        for row, batch in enumerate(batched(group, 2)):
            for column, player_achievement in enumerate(batch):
                widget = AchievementWidget(player_achievement, self.img_dler)
                widget.setup()
                layout.addWidget(widget, row, column)
        return layout

    def add_achievement_group(self, name: str, group: list[PlayerAchievement]) -> None:
        label = self.create_group_title_label(f"{name} ({len(group)})")
        self.layout.addWidget(label)
        self.layout.addWidget(self.create_hline())
        group_layout = self.create_achievement_group_layout(group)
        self.layout.addLayout(group_layout)

    def group_achievements(
            self,
            player_achievements: Iterator[PlayerAchievement],
    ) -> AchievementGroup:
        unlocked, locked, progressed_any_percent = [], [], []
        for player_achievement in player_achievements:
            progressed_any_percent.append(player_achievement.achievement.xd)
            if player_achievement.current_state == State.UNLOCKED:
                unlocked.append(player_achievement)
            else:
                locked.append(player_achievement)
        locked.extend((
            self.mock_player_achievement(entry)
            for entry in self.all_achievements
            if entry.xd not in progressed_any_percent
        ))
        return AchievementGroup(locked, unlocked)

    def on_player_achievements_ready(
            self,
            player_achievements: Iterator[PlayerAchievement],
    ) -> None:
        locked, unlocked = self.group_achievements(player_achievements)
        self.add_achievement_group("Unlocked", unlocked)
        self.add_achievement_group("Locked", locked)
        self._loaded = True


class AchievementGroup(NamedTuple):
    locked: list[PlayerAchievement]
    unlocked: list[PlayerAchievement]
