from PyQt6 import QtCore
from PyQt6 import QtWidgets


# TODO: probably create a common ancestor of ChatLineEdit and this
class LeaderboardLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.completionStarted = False
        self.currenLocalChatter = None
        self.LocalNameList = []
        self.completionList = None

    def set_completion_list(self, list_):
        self.completionList = list_

    def event(self, event):
        if event.type() == QtCore.QEvent.Type.KeyPress:
            # Swallow a selection of keypresses that we want for our history
            # support.
            if event.key() == QtCore.Qt.Key.Key_Tab:
                self.try_completion()
                return True
            else:
                self.cancel_completion()
                return QtWidgets.QLineEdit.event(self, event)

        # All other events (non-keypress)
        return QtWidgets.QLineEdit.event(self, event)

    def try_completion(self):
        if not self.completionStarted:
            # no completion on empty line
            if self.text() == "":
                return
            # no completion if last character is a space
            if self.text().rfind(" ") == (len(self.text()) - 1):
                return

            self.completionStarted = True
            self.LocalNameList = []

            # make a copy of users because the list might change frequently
            # giving all kind of problems
            if self.completionList is not None:
                for name in self.completionList:
                    if name.lower().startswith(self.text().lower()):
                        self.LocalNameList.append(name)

            if len(self.LocalNameList) > 0:
                self.LocalNameList.sort(key=lambda login: login.lower())
                self.currenLoginIndex = 0
                self.setText(self.LocalNameList[self.currenLoginIndex])
            else:
                self.currenLoginIndex = None
        else:
            if self.currenLoginIndex is not None:
                self.currenLoginIndex += 1
                self.currenLoginIndex %= len(self.LocalNameList)
                self.setText(self.LocalNameList[self.currenLoginIndex])

    def cancel_completion(self):
        self.completionStarted = False
