"""
Settings for notifications: if a player comes online
"""
from PyQt6 import QtCore

import notifications as ns
import util
from config import Settings
from notifications.ns_hook import NsHook


class NsHookPartyInvite(NsHook):
    def __init__(self):
        NsHook.__init__(self, ns.Notifications.PARTY_INVITE)
        self.button.setEnabled(True)
        self.dialog = PartyInviteDialog(self, self.eventType)
        self.button.clicked.connect(self.dialog.show)


FormClass, BaseClass = util.THEME.loadUiType(
    "notification_system/party_invite.ui",
)


class PartyInviteDialog(FormClass, BaseClass):
    def __init__(self, parent, eventType):
        BaseClass.__init__(self)
        self.parent = parent
        self.eventType = eventType
        self._settings_key = 'notifications/{}'.format(eventType)
        self.setupUi(self)

        # remove help button
        self.setWindowFlags(
            self.windowFlags() & (~QtCore.Qt.WindowType.WindowContextHelpButtonHint),
        )

        self.loadSettings()

    def loadSettings(self):
        self.mode = Settings.get(self._settings_key + '/mode', 'friends')

        if self.mode == 'friends':
            self.radioButtonFriends.setChecked(True)
        else:
            self.radioButtonAll.setChecked(True)
        self.parent.mode = self.mode

    def saveSettings(self):
        Settings.set(self._settings_key + '/mode', self.mode)
        self.parent.mode = self.mode

    @QtCore.pyqtSlot()
    def on_btnSave_clicked(self):
        self.mode = 'friends' if self.radioButtonFriends.isChecked() else 'all'
        self.saveSettings()
        self.hide()
