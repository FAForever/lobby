from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from src import util


class TourneyItemDelegate(QtWidgets.QStyledItemDelegate):
    # colors = json.loads(util.THEME.readfile("client/colors.json"))

    def __init__(self, *args, **kwargs):
        QtWidgets.QStyledItemDelegate.__init__(self, *args, **kwargs)
        self.height = 125

    def paint(self, painter, option, index, *args, **kwargs):
        self.initStyleOption(option, index)

        painter.save()

        html = QtGui.QTextDocument()
        html.setHtml(option.text)
        if self.height < html.size().height():
            self.height = html.size().height()

        option.text = ""
        option.widget.style().drawControl(
            QtWidgets.QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget,
        )

        # Description
        painter.translate(option.rect.left(), option.rect.top())
        # painter.fillRect(QtCore.QRect(0, 0, option.rect.width(),
        #                 option.rect.height()), QtGui.QColor(36, 61, 75, 150))
        clip = QtCore.QRectF(0, 0, option.rect.width(), option.rect.height())
        html.drawContents(painter, clip)

        painter.restore()

    def sizeHint(self, option, index, *args, **kwargs):
        self.initStyleOption(option, index)
        html = QtGui.QTextDocument()
        html.setHtml(option.text)
        return QtCore.QSize(
            int(html.size().width()), int(html.size().height()),
        )


class TourneyItem(QtWidgets.QListWidgetItem):
    FORMATTER_SWISS_OPEN = str(
        util.THEME.readfile("tournaments/formatters/open.qthtml"),
    )

    def __init__(self, parent, uid, *args, **kwargs):
        QtWidgets.QListWidgetItem.__init__(self, *args, **kwargs)

        self.uid = int(uid)

        self.parent = parent

        self.type = None
        self.client = None
        self.title = None
        self.description = None
        self.state = None
        self.players = []
        self.playersname = []

        self.viewtext = ""
        self.height = 40
        self.setHidden(True)

    def update(self, message, client):
        """
        Updates this item from the message dictionary supplied
        """
        self.client = client
        old_state = self.state
        self.state = message.get('state', "close")

        """ handling the listing of the tournament """
        self.title = message['name']
        self.type = message['type']
        self.url = message['url']
        self.description = message.get('description', "")
        self.players = message.get('participants', [])

        if old_state != self.state and self.state == "started":
            # create a widget and add it to the parent's tabs
            # anyway, this tournaments feature most likely won't return
            ...

        self.playersname = []
        for player in self.players:
            self.playersname.append(player["name"])
            if (
                old_state != self.state
                and self.state == "started"
                and player["name"] == self.client.login
            ):
                channel = "#" + self.title.replace(" ", "_")
                self.client.auto_join.emit([channel])
                QtWidgets.QMessageBox.information(
                    self.client,
                    "Tournament started !",
                    (
                        "Your tournament has started !\n"
                        "You have automatically joined the tournament channel."
                    ),
                )

        playerstring = "<br/>".join(self.playersname)

        self.viewtext = self.FORMATTER_SWISS_OPEN.format(
            title=self.title, description=self.description,
            numreg=str(len(self.players)), playerstring=playerstring,
        )
        self.setText(self.viewtext)

    def display(self):
        return self.viewtext

    def data(self, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.display()
        elif role == QtCore.Qt.ItemDataRole.UserRole:
            return self
        return super(TourneyItem, self).data(role)

    def __ge__(self, other):
        """ Comparison operator used for item list sorting """
        return not self.__lt__(other)

    def __lt__(self, other):
        """ Comparison operator used for item list sorting """
        if not self.client:
            return True  # If not initialized...
        if not other.client:
            return False

        # Default: Alphabetical
        return self.title.lower() < other.title.lower()
