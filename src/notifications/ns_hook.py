"""
Setting Model class.
All Event Types (Notifications) are customizable.
Required are "popup, sound, enabled" settings.
You can add custom settings over the "settings" button.
connect on clicked event some actions, e.g.

self.button.clicked.connect(self.dialog.show)
"""
from PyQt6 import QtWidgets

from config import Settings


class NsHook():
    def __init__(self, eventType):
        self.eventType = eventType
        self._settings_key = 'notifications/{}'.format(eventType)
        self.loadSettings()
        self.button = QtWidgets.QPushButton('More')
        self.button.setEnabled(False)

    def loadSettings(self) -> None:
        self.popup = Settings.get(f"{self._settings_key}/popup", default=True, type=bool)
        self.sound = Settings.get(f"{self._settings_key}/sound", default=True, type=bool)
        self.ingame = Settings.get(f"{self._settings_key}/ingame", default=False, type=bool)

    def saveSettings(self) -> None:
        Settings.set(f"{self._settings_key}/popup", self.popup)
        Settings.set(f"{self._settings_key}/sound", self.sound)
        Settings.set(f"{self._settings_key}/ingame", self.ingame)

    def getEventDisplayName(self):
        return self.eventType

    def popupEnabled(self):
        return self.popup

    def switchPopup(self):
        self.popup = not self.popup
        self.saveSettings()

    def soundEnabled(self):
        return self.sound

    def ingame_allowed(self) -> bool:
        return self.ingame

    def switch_ingame(self) -> None:
        self.ingame = not self.ingame
        self.saveSettings()

    def switchSound(self):
        self.sound = not self.sound
        self.saveSettings()

    def settings(self):
        return self.button
