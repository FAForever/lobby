
import os
import urllib.parse

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from src import util
from src.api.models.ModType import ModType
from src.util import strtodate
from src.vaults.modvault.moditem import ModListItem

from .modvault import utils

FormClass, BaseClass = util.THEME.loadUiType("vaults/modvault/mod.ui")


class ModWidget(FormClass, BaseClass):
    ICONSIZE = QtCore.QSize(100, 100)

    def __init__(self, parent: QtWidgets.QWidget, mod_item: ModListItem, *args, **kwargs) -> None:
        BaseClass.__init__(self, *args, **kwargs)

        self.setupUi(self)
        self.parent = parent

        util.THEME.stylesheets_reloaded.connect(self.load_stylesheet)
        self.load_stylesheet()

        self.mod = mod_item.item_info
        self.mod_version = mod_item.item_version

        self.setWindowTitle(self.mod.display_name)

        self.Title.setText(self.mod.display_name)
        self.Description.setText(self.mod_version.description)
        modtext = ""
        if self.mod_version.modtype == ModType.UI:
            modtext = "UI mod"
        self.Info.setText(
            f"{modtext}\nBy {self.mod.author}\nUploaded {self.mod_version.create_time}",
        )
        thumbnail = utils.getIcon(
            os.path.basename(urllib.parse.unquote(self.mod_version.thumbnail_url)),
        )
        if thumbnail is None:
            self.Picture.setPixmap(util.THEME.pixmap("games/unknown_map.png"))
        else:
            pixmap = util.THEME.pixmap(thumbnail, False)
            self.Picture.setPixmap(pixmap.scaled(self.ICONSIZE))

        # ensure that pixmap is set
        if self.Picture.pixmap() is None or self.Picture.pixmap().isNull():
            self.Picture.setPixmap(util.THEME.pixmap("games/unknown_map.png"))

        # self.Comments.setItemDelegate(CommentItemDelegate(self))
        # self.BugReports.setItemDelegate(CommentItemDelegate(self))

        self.tabWidget.setEnabled(False)

        if self.mod_version.uid in self.parent.uids:
            self.DownloadButton.setText("Remove Mod")
        self.DownloadButton.clicked.connect(self.download)

        # self.likeButton.clicked.connect(self.like)
        # self.LineComment.returnPressed.connect(self.addComment)
        # self.LineBugReport.returnPressed.connect(self.addBugReport)

        # for item in mod.comments:
        #     comment = CommentItem(self,item["uid"])
        #     comment.update(item)
        #     self.Comments.addItem(comment)
        # for item in mod.bugreports:
        #     comment = CommentItem(self,item["uid"])
        #     comment.update(item)
        #     self.BugReports.addItem(comment)

        self.likeButton.setEnabled(False)
        self.LineComment.setEnabled(False)
        self.LineBugReport.setEnabled(False)

    def load_stylesheet(self):
        self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

    @QtCore.pyqtSlot()
    def download(self) -> None:
        if self.mod_version.uid not in self.parent.uids:
            self.parent.downloadMod(self.mod_version.download_url, self.mod.display_name)
            self.done(1)
        else:
            show = QtWidgets.QMessageBox.question(
                self.parent.client,
                "Delete Mod",
                "Are you sure you want to delete this mod?",
                QtWidgets.QMessageBox.StandardButton.Yes,
                QtWidgets.QMessageBox.StandardButton.No,
            )
            if show == QtWidgets.QMessageBox.StandardButton.Yes:
                self.parent.removeMod(self.mod.display_name, self.mod_version.uid)
                self.done(1)

    @QtCore.pyqtSlot()
    def addComment(self):
        # TODO: implement this with the use of API
        ...

    @QtCore.pyqtSlot()
    def addBugReport(self):
        # TODO: implement this with the use of API (if possible)
        ...

    @QtCore.pyqtSlot()
    def like(self):
        # TODO: implement this with the use of API
        ...


class CommentItemDelegate(QtWidgets.QStyledItemDelegate):
    TEXTWIDTH = 350
    TEXTHEIGHT = 60

    def __init__(self, *args, **kwargs):
        QtWidgets.QStyledItemDelegate.__init__(self, *args, **kwargs)

    def paint(self, painter, option, index, *args, **kwargs):
        self.initStyleOption(option, index)

        painter.save()

        html = QtGui.QTextDocument()
        html.setHtml(option.text)

        option.text = ""
        option.widget.style().drawControl(
            QtWidgets.QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget,
        )

        # Description
        painter.translate(option.rect.left() + 10, option.rect.top() + 10)
        clip = QtCore.QRectF(0, 0, option.rect.width(), option.rect.height())
        html.drawContents(painter, clip)

        painter.restore()

    def sizeHint(self, option, index, *args, **kwargs):
        self.initStyleOption(option, index)

        html = QtGui.QTextDocument()
        html.setHtml(option.text)
        html.setTextWidth(self.TEXTWIDTH)
        return QtCore.QSize(self.TEXTWIDTH, self.TEXTHEIGHT)


class CommentItem(QtWidgets.QListWidgetItem):
    FORMATTER_COMMENT = str(
        util.THEME.readfile("vaults/modvault/comment.qthtml"),
    )

    def __init__(self, parent, uid, *args, **kwargs):
        QtWidgets.QListWidgetItem.__init__(self, *args, **kwargs)

        self.parent = parent
        self.uid = uid
        self.text = ""
        self.author = ""
        self.date = None

    def update(self, dic):
        self.text = dic["text"]
        self.author = dic["author"]
        self.date = strtodate(dic["date"])
        self.setText(
            self.FORMATTER_COMMENT.format(
                text=self.text,
                author=self.author,
                date=str(self.date),
            ),
        )

    def __ge__(self, other):
        return self.date > other.date

    def __lt__(self, other):
        return self.date <= other.date
