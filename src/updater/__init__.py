from PyQt6.QtCore import QObject
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QDialog
from PyQt6.QtWidgets import QMessageBox
from semantic_version import Version

from src.updater.base import Releases
from src.updater.base import UpdateChecker
from src.updater.base import UpdateNotifier
from src.updater.base import UpdateSettings
from src.updater.widgets import UpdateDialog
from src.updater.widgets import UpdateSettingsDialog


class ClientUpdateTools(QObject):
    mandatory_update_aborted = pyqtSignal()

    def __init__(
        self, update_settings, checker, notifier, dialog, parent_widget,
    ):
        QObject.__init__(self)
        self.update_settings = update_settings
        self.checker = checker
        self.notifier = notifier
        self.dialog = dialog
        self.parent_widget = parent_widget
        self.notifier.update.connect(self._handle_update)

    @classmethod
    def build(cls, current_version, parent_widget, network_manager):
        current_version = Version(current_version)
        update_settings = UpdateSettings()
        checker = UpdateChecker.build(
            current_version=current_version,
            settings=update_settings,
            network_manager=network_manager,
        )
        notifier = UpdateNotifier(update_settings, checker)
        dialog = UpdateDialog.build(
            update_settings, parent_widget, current_version,
            network_manager=network_manager,
        )
        return cls(update_settings, checker, notifier, dialog, parent_widget)

    def _handle_update(self, releases: Releases, mandatory: bool) -> None:
        branch = self.update_settings.updater_branch.to_reltype()
        versions = releases.versions(
            branch, self.update_settings.updater_downgrade,
        )
        if not versions:
            QMessageBox.information(
                self.parent_widget, "No updates found",
                "No client updates were found.",
            )
            return
        self.dialog.setup(releases)
        result = self.dialog.exec()
        if result is QDialog.DialogCode.Rejected and mandatory:
            self.mandatory_update_aborted.emit()

    def settings_dialog(self):
        return UpdateSettingsDialog(self.parent_widget, self.update_settings)
