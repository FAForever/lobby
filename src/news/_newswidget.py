import logging

from PyQt6 import QtWidgets
from PyQt6.QtCore import QByteArray
from PyQt6.QtCore import QPoint
from PyQt6.QtCore import QSize
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QImage
from PyQt6.QtGui import QTextDocument
from PyQt6.QtNetwork import QNetworkAccessManager
from PyQt6.QtNetwork import QNetworkReply
from PyQt6.QtNetwork import QNetworkRequest

import util
from config import Settings

from .newsitem import NewsItem
from .newsitem import NewsItemDelegate
from .newsmanager import NewsManager

logger = logging.getLogger(__name__)


FormClass, BaseClass = util.THEME.loadUiType("news/news.ui")


class NewsWidget(FormClass, BaseClass):
    CSS = util.THEME.readstylesheet('news/news_style.css')

    HTML = util.THEME.readfile('news/news_page.html')

    def __init__(self, *args, **kwargs) -> None:
        BaseClass.__init__(self, *args, **kwargs)

        self.setupUi(self)

        self.nam = QNetworkAccessManager()
        self.reply: QNetworkReply | None = None

        self.newsManager = NewsManager(self)
        self.newsItems = []
        self.images = {}

        # open all links in external browser
        self.newsTextBrowser.setOpenExternalLinks(True)

        self.settingsFrame.hide()
        self.hideNewsEdit.setText(Settings.get('news/hideWords', ""))

        self.newsList.setIconSize(QSize(0, 0))
        self.newsList.setItemDelegate(NewsItemDelegate(self))
        self.newsList.currentItemChanged.connect(self.itemChanged)
        self.newsSettings.pressed.connect(self.showSettings)
        self.showAllButton.pressed.connect(self.showAll)
        self.hideNewsEdit.textEdited.connect(self.updateNewsFilter)
        self.hideNewsEdit.cursorPositionChanged.connect(self.showEditToolTip)

    def addNews(self, newsPost):
        newsItem = NewsItem(newsPost, self.newsList)
        self.newsItems.append(newsItem)

    def updateNews(self) -> None:
        self.hider.hide(self.newsTextBrowser)
        self.newsItems = []
        self.newsList.clear()
        self.newsManager.WpApi.download()

    def download_image(self, img_url: QUrl) -> None:
        request = QNetworkRequest(img_url)
        self.reply = self.nam.get(request)
        self.reply.finished.connect(self.item_image_downloaded)

    def add_image_resource(self, img_url: QUrl, image_data: QByteArray) -> None:
        img = QImage()
        img.loadFromData(image_data)
        scaled = img.scaled(QSize(900, 500))

        self.images[img_url] = scaled
        self.newsTextBrowser.document().addResource(
            QTextDocument.ResourceType.ImageResource,
            img_url,
            scaled,
        )

    def item_image_downloaded(self) -> None:
        if self.reply.error() is not self.reply.NetworkError.NoError:
            return
        self.add_image_resource(self.reply.request().url(), self.reply.readAll())
        self.show_newspage()

    def itemChanged(self, current: NewsItem | None, previous: NewsItem | None) -> None:
        if current is None:
            return
        url = QUrl(current.newsPost["img_url"])
        if url in self.images:
            self.show_newspage()
        else:
            self.download_image(url)

    def show_newspage(self) -> None:
        current = self.newsList.currentItem()

        if current.newsPost['external_link'] == '':
            external_link = current.newsPost['link']
        else:
            external_link = current.newsPost['external_link']

        content = current.newsPost["excerpt"].strip().removeprefix("<p>").removesuffix("</p>")
        html = self.HTML.format(
            style=self.CSS,
            title=current.newsPost['title'],
            content=content,
            img_source=current.newsPost["img_url"],
            external_link=external_link,
        )
        self.newsTextBrowser.setHtml(html)

    def showAll(self):
        for item in self.newsItems:
            item.setHidden(False)
        self.updateLabel(0)

    def showEditToolTip(self) -> None:
        """
        Default tooltips are too slow and disappear when user starts typing
        """
        widget = self.hideNewsEdit
        position = widget.mapToGlobal(
            QPoint(0 + widget.width(), 0 - widget.height() / 2),
        )
        QtWidgets.QToolTip.showText(
            position,
            "To separate multiple words use commas: nomads,server,dev",
        )

    def showSettings(self):
        if self.settingsFrame.isHidden():
            self.settingsFrame.show()
        else:
            self.settingsFrame.hide()

    def updateNewsFilter(self, text=False):
        if text is not False:
            Settings.set('news/hideWords', text)

        filterList = Settings.get('news/hideWords', "").lower().split(",")
        newsHidden = 0

        if filterList[0]:
            for item in self.newsItems:
                for word in filterList:
                    if word in item.text().lower():
                        item.setHidden(True)
                        newsHidden += 1
                        break
                    else:
                        item.setHidden(False)
        else:
            for item in self.newsItems:
                item.setHidden(False)

        self.updateLabel(newsHidden)

    def updateLabel(self, number):
        self.totalHidden.setText("NEWS HIDDEN: " + str(number))
