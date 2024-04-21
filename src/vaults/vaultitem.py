from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtWidgets import QStyle
from PyQt6.QtWidgets import QStyledItemDelegate

import util
from api.models.Map import Map
from api.models.Mod import Mod
from downloadManager import Downloader
from downloadManager import DownloadRequest

if TYPE_CHECKING:
    from vaults.vault import Vault


class VaultListItem(QListWidgetItem):
    TEXTWIDTH = 230
    ICONSIZE = 100
    PADDING = 10

    def __init__(self, parent: Vault, item_info: Mod | Map, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.setHidden(True)

        self.item_info = item_info
        self.item_version = item_info.version

        self._preview_dler = Downloader(util.CACHE_DIR)
        self._item_dl_request = DownloadRequest()
        self._item_dl_request.done.connect(self._on_item_downloaded)

    def update(self):
        self.ensure_icon()
        self.update_visibility()

    def set_item_icon(self, filename: str, themed: bool = True) -> None:
        icon = util.THEME.icon(filename)
        if not themed:
            pixmap = QtGui.QPixmap(filename)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(QtCore.QSize(self.ICONSIZE, self.ICONSIZE))
                icon.addPixmap(scaled_pixmap)
        self.setIcon(icon)

    def ensure_icon(self):
        if self.icon() is None or self.icon().isNull():
            self.set_item_icon("games/unknown_map.png")

    def _on_item_downloaded(self, mapname: str, result: tuple[str, bool]) -> None:
        filename, themed = result
        self.set_item_icon(filename, themed)
        self.ensure_icon()

    def should_be_hidden(self) -> bool:
        return not self.should_be_visible()

    def should_be_visible(self) -> bool:
        return True

    def update_visibility(self) -> None:
        self.setHidden(self.should_be_hidden())
        if len(self.item_version.description) < 200:
            trimmed_description = self.item_version.description
        else:
            trimmed_description = f"{self.item_version.description[:197]}..."
        self.setToolTip('<p width="230">{}</p>'.format(trimmed_description))

    def __ge__(self, other: VaultListItem) -> bool:
        return not self.__lt__(self, other)

    def __lt__(self, other: VaultListItem) -> bool:
        if self.parent.sortType == "alphabetical":
            return self._lt_alphabetical(other)
        elif self.parent.sortType == "rating":
            return self._lt_rating(other)
        elif self.parent.sortType == "date":
            return self._lt_date(other)
        return True

    def _lt_date(self, other: VaultListItem) -> bool:
        if self.item_version.create_time == other.item_version.create_time:
            if self.item_version.update_time == other.item_version.update_time:
                return self._lt_alphabetical(other)
            return self.item_version.update_time < other.item_version.update_time
        return self.item_version.create_time < other.item_version.create_time

    def _lt_alphabetical(self, other: VaultListItem) -> bool:
        return self.item_info.display_name.lower() > other.item_info.display_name.lower()

    def _lt_rating(self, other: VaultListItem) -> bool:
        review = self.item_info.reviews_summary
        other_review = other.item_info.reviews_summary

        if review is None:
            return other_review is not None
        if other_review is None:
            return review is None

        if review.average_score == other_review.average_score:
            if review.num_reviews == other_review.num_reviews:
                return self._lt_alphabetical(other)
            return review.num_reviews < other_review.num_reviews

        return review.average_score < other_review.average_score


class VaultItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index, *args, **kwargs):
        self.initStyleOption(option, index)

        painter.save()

        html = QtGui.QTextDocument()
        html.setHtml(option.text)

        icon = QtGui.QIcon(option.icon)
        iconsize = QtCore.QSize(VaultListItem.ICONSIZE, VaultListItem.ICONSIZE)

        # clear icon and text before letting the control draw itself because
        # we're rendering these parts ourselves
        option.icon = QtGui.QIcon()
        option.text = ""
        control_element = QStyle.ControlElement.CE_ItemViewItem
        option.widget.style().drawControl(control_element, option, painter, option.widget)

        # Shadow
        painter.fillRect(
            option.rect.left() + 7,
            option.rect.top() + 7,
            iconsize.width(),
            iconsize.height(),
            QtGui.QColor("#202020"),
        )

        iconrect = QtCore.QRect(option.rect.adjusted(3, 3, 0, 0))
        iconrect.setSize(iconsize)
        # Icon
        alignment = QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        icon.paint(painter, iconrect, alignment)

        # Frame around the icon
        pen = QtGui.QPen()
        pen.setWidth(1)
        # FIXME: This needs to come from theme.
        pen.setBrush(QtGui.QColor("#303030"))

        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawRect(iconrect)

        # Description
        painter.translate(
            option.rect.left() + iconsize.width() + 10, option.rect.top() + 4,
        )
        clip = QtCore.QRectF(
            0, 0, option.rect.width() - iconsize.width() - 15,
            option.rect.height(),
        )
        html.drawContents(painter, clip)

        painter.restore()

    def sizeHint(self, option, index, *args, **kwargs):
        self.initStyleOption(option, index)

        html = QtGui.QTextDocument()
        html.setHtml(option.text)
        html.setTextWidth(VaultListItem.TEXTWIDTH)
        return QtCore.QSize(
            (
                VaultListItem.ICONSIZE
                + VaultListItem.TEXTWIDTH
                + VaultListItem.PADDING
            ),
            VaultListItem.ICONSIZE + VaultListItem.PADDING,
        )
