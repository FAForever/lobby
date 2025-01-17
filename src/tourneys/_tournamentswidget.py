
from PyQt6 import QtCore
from PyQt6 import QtWidgets

from src import secondaryServer
from src import util
from src.tourneys.tourneyitem import TourneyItem
from src.tourneys.tourneyitem import TourneyItemDelegate

FormClass, BaseClass = util.THEME.loadUiType("tournaments/tournaments.ui")


class TournamentsWidget(FormClass, BaseClass):
    """ list and manage the main tournament lister """

    def __init__(self, client, *args, **kwargs):
        BaseClass.__init__(self, *args, **kwargs)

        self.setupUi(self)

        self.client = client

        # tournament server
        self.tourneyServer = secondaryServer.SecondaryServer(
            "Tournament", 11001, self,
        )
        self.tourneyServer.setInvisible()

        # Dictionary containing our actual tournaments.
        self.tourneys = {}

        self.tourneyList.setItemDelegate(TourneyItemDelegate(self))

        self.tourneyList.itemDoubleClicked.connect(self.tourneyDoubleClicked)

        self.tourneysTab = {}

        util.THEME.stylesheets_reloaded.connect(self.load_stylesheet)
        self.load_stylesheet()

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect(self.updateTournaments)
        self.updateTimer.start(600000)

    def load_stylesheet(self):
        self.setStyleSheet(
            util.THEME.readstylesheet("tournaments/formatters/style.css"),
        )

    def showEvent(self, event):
        self.updateTournaments()
        return BaseClass.showEvent(self, event)

    def updateTournaments(self):
        self.tourneyServer.send(dict(command="get_tournaments"))

    @QtCore.pyqtSlot(QtWidgets.QListWidgetItem)
    def tourneyDoubleClicked(self, item):
        """
        Slot that attempts to join or leave a tournament.
        """
        if self.client.login not in item.playersname:
            reply = QtWidgets.QMessageBox.question(
                self.client,
                "Register",
                "Do you want to register to this tournament ?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.tourneyServer.send(
                    dict(
                        command="add_participant",
                        uid=item.uid,
                        login=self.client.login,
                    ),
                )

        else:
            reply = QtWidgets.QMessageBox.question(
                self.client,
                "Register",
                "Do you want to leave this tournament ?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.tourneyServer.send(
                    dict(
                        command="remove_participant",
                        uid=item.uid,
                        login=self.client.login,
                    ),
                )

    def handle_tournaments_info(self, message):
        # self.tourneyList.clear()
        tournaments = message["data"]
        for uid in tournaments:
            if uid not in self.tourneys:
                self.tourneys[uid] = TourneyItem(self, uid)
                self.tourneyList.addItem(self.tourneys[uid])
                self.tourneys[uid].update(tournaments[uid], self.client)
            else:
                self.tourneys[uid].update(tournaments[uid], self.client)
