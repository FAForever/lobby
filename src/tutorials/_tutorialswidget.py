import logging
import os

from PyQt6 import QtCore
from PyQt6 import QtWidgets
from PyQt6.QtNetwork import QNetworkAccessManager
from PyQt6.QtNetwork import QNetworkReply
from PyQt6.QtNetwork import QNetworkRequest

import fa
import util
from tutorials.tutorialitem import TutorialItem
from tutorials.tutorialitem import TutorialItemDelegate

logger = logging.getLogger(__name__)

FormClass, BaseClass = util.THEME.loadUiType("tutorials/tutorials.ui")


class TutorialsWidget(FormClass, BaseClass):
    def __init__(self, client, *args, **kwargs):
        BaseClass.__init__(self, *args, **kwargs)

        self.setupUi(self)

        self.client = client

        self.sections = {}
        self.tutorials = {}

        self.client.lobby_info.tutorialsInfo.connect(self.processTutorialInfo)

        logger.info("Tutorials instantiated.")

    def finishReplay(self, reply):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            QtWidgets.QMessageBox.warning(
                self, "Network Error", reply.errorString(),
            )
        else:
            filename = os.path.join(util.CACHE_DIR, str("tutorial.fafreplay"))
            replay = QtCore.QFile(filename)
            replay.open(QtCore.QIODevice.OpenModeFlag.WriteOnly | QtCore.QIODevice.Text)
            replay.write(reply.readAll())
            replay.close()

            fa.replay(filename, True)

    def tutorialClicked(self, item):

        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self.finishReplay)
        self.nam.get(QNetworkRequest(QtCore.QUrl(item.url)))

    def processTutorialInfo(self, message):
        """
        Two type here : section or tutorials.
        Sections are defining the differents type of tutorials
        """

        logger.debug("Processing TutorialInfo")

        if "section" in message:
            section = message["section"]
            desc = message["description"]

            area = util.THEME.loadUi("tutorials/tutorialarea.ui")
            tabIndex = self.addTab(area, section)
            self.setTabToolTip(tabIndex, desc)

            # Set up the List that contains the tutorial items
            area.listWidget.setItemDelegate(TutorialItemDelegate(self))
            area.listWidget.itemDoubleClicked.connect(self.tutorialClicked)

            self.sections[section] = area.listWidget

        elif "tutorial" in message:
            tutorial = message["tutorial"]
            section = message["tutorial_section"]

            if section in self.sections:
                self.tutorials[tutorial] = TutorialItem(tutorial)
                self.tutorials[tutorial].update(message, self.client)

                self.sections[section].addItem(self.tutorials[tutorial])
