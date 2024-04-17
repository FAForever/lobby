from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

import util
from downloadManager import Downloader
from downloadManager import DownloadRequest


class VaultItem(QtWidgets.QListWidgetItem):
    TEXTWIDTH = 230
    ICONSIZE = 100
    PADDING = 10

    def __init__(self, parent, *args, **kwargs):
        QtWidgets.QListWidgetItem.__init__(self, *args, **kwargs)
        self.parent = parent

        self.name = ""
        self.description = ""
        self.trimmedDescription = ""
        self.version = 0
        self.rating = 0
        self.reviews = 0
        self.date = None

        self.itemType_ = ""
        self.color = "white"

        self.link = ""
        self.setHidden(True)

        self._preview_dler = Downloader(util.CACHE_DIR)
        self._item_dl_request = DownloadRequest()
        self._item_dl_request.done.connect(self._on_item_downloaded)

    def update(self):
        self.ensureIcon()
        self.updateVisibility()

    def setItemIcon(self, filename, themed=True):
        icon = util.THEME.icon(filename)
        if not themed:
            pixmap = QtGui.QPixmap(filename)
            if not pixmap.isNull():
                icon.addPixmap(
                    pixmap.scaled(
                        QtCore.QSize(self.ICONSIZE, self.ICONSIZE),
                    ),
                )
        self.setIcon(icon)

    def ensureIcon(self):
        if self.icon() is None or self.icon().isNull():
            self.setItemIcon("games/unknown_map.png")

    def _on_item_downloaded(self, mapname, result):
        filename, themed = result
        self.setItemIcon(filename, themed)
        self.ensureIcon()

    def updateVisibility(self):
        self.setHidden(not self.shouldBeVisible())
        if len(self.description) < 200:
            self.trimmedDescription = self.description
        else:
            self.trimmedDescription = self.description[:197] + "..."

        self.setToolTip('<p width="230">{}</p>'.format(self.description))

    def __ge__(self, other):
        return not self.__lt__(self, other)

    def __lt__(self, other):
        if self.parent.sortType == "alphabetical":
            return self.name.lower() > other.name.lower()
        elif self.parent.sortType == "rating":
            if self.rating == other.rating:
                if self.reviews == other.reviews:
                    return self.name.lower() > other.name.lower()
                return self.reviews < other.reviews
            return self.rating < other.rating
        elif self.parent.sortType == "size":
            if self.height * self.width == other.height * other.width:
                return self.name.lower() > other.name.lower()
            return self.height * self.width < other.height * other.width
        elif self.parent.sortType == "date":
            if self.date is None:
                return other.date is not None
            if self.date == other.date:
                return self.name.lower() > other.name.lower()
            return self.date < other.date


class VaultItemDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, *args, **kwargs):
        QtWidgets.QStyledItemDelegate.__init__(self, *args, **kwargs)

    def paint(self, painter, option, index, *args, **kwargs):
        self.initStyleOption(option, index)

        painter.save()

        html = QtGui.QTextDocument()
        html.setHtml(option.text)

        icon = QtGui.QIcon(option.icon)
        iconsize = QtCore.QSize(VaultItem.ICONSIZE, VaultItem.ICONSIZE)

        # clear icon and text before letting the control draw itself because
        # we're rendering these parts ourselves
        option.icon = QtGui.QIcon()
        option.text = ""
        option.widget.style().drawControl(
            QtWidgets.QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget,
        )

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
        html.setTextWidth(VaultItem.TEXTWIDTH)
        return QtCore.QSize(
            (
                VaultItem.ICONSIZE
                + VaultItem.TEXTWIDTH
                + VaultItem.PADDING
            ),
            VaultItem.ICONSIZE + VaultItem.PADDING,
        )
