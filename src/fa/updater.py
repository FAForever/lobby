
"""
This is the FORGED ALLIANCE updater.

It ensures, through communication with faforever.com, that Forged Alliance
is properly updated, patched, and all required files for a given mod are
installed

@author thygrrr
"""
import logging
import os
import shutil
import stat
import time
from enum import Enum
from functools import partial

from PyQt6.QtCore import QObject
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QDialog
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtWidgets import QProgressDialog

import util
from api.featured_mod_api import FeaturedModApiConnector
from api.featured_mod_api import FeaturedModFilesApiConnector
from api.models.FeaturedMod import FeaturedMod
from api.models.FeaturedModFile import FeaturedModFile
from api.sim_mod_updater import SimModFiles
from config import Settings
from fa.utils import unpack_movies_and_sounds
from vaults.dialogs import download_file
from vaults.modvault import utils

logger = logging.getLogger(__name__)

# This contains a complete dump of everything that was supplied to logOutput
debugLog = []


FormClass, BaseClass = util.THEME.loadUiType("fa/updater/updater.ui")


class UpdaterProgressDialog(FormClass, BaseClass):
    def __init__(self, parent):
        BaseClass.__init__(self, parent)
        self.setupUi(self)
        self.logPlainTextEdit.setVisible(False)
        self.adjustSize()
        self.watches = []

    @pyqtSlot(str)
    def appendLog(self, text):
        self.logPlainTextEdit.appendPlainText(text)

    @pyqtSlot(QObject)
    def addWatch(self, watch):
        self.watches.append(watch)
        watch.finished.connect(self.watchFinished)

    @pyqtSlot()
    def watchFinished(self) -> None:
        for watch in self.watches:
            if not watch.isFinished():
                return
        # equivalent to self.accept(), but clearer
        self.done(QDialog.DialogCode.Accepted)


def clearLog():
    global debugLog
    debugLog = []


def log(string):
    logger.debug(string)
    debugLog.append(str(string))


def dumpPlainText():
    return "\n".join(debugLog)


def dumpHTML():
    return "<br/>".join(debugLog)


# A set of exceptions we use to see what goes wrong during asynchronous data
# transfer waits
class UpdaterCancellation(Exception):
    pass


class UpdaterFailure(Exception):
    pass


class UpdaterTimeout(Exception):
    pass


class UpdaterResult(Enum):
    SUCCESS = 0  # Update successful
    NONE = -1  # Update operation is still ongoing
    FAILURE = 1  # An error occured during updating
    CANCEL = 2  # User cancelled the download process
    ILLEGAL = 3  # User has the wrong version of FA
    BUSY = 4  # Server is currently busy
    PASS = 5  # User refuses to update by canceling the wizard


class Updater(QObject):
    """
    This is the class that does the actual installation work.
    """

    def __init__(
        self,
        featured_mod: str,
        version: int | None = None,
        modversions: dict | None = None,
        sim_mod: tuple[str, str] | None = None,
        silent: bool = False,
        *args,
        **kwargs,
    ):
        """
        Constructor
        """
        super().__init__(*args, **kwargs)

        self.featured_mod = featured_mod
        self.version = version
        self.modversions = modversions
        self.sim_mod = sim_mod
        self.silent = silent

        self.result = UpdaterResult.NONE

        self.keep_cache = not Settings.get(
            'cache/do_not_keep', type=bool, default=True,
        )
        self.in_session_cache = Settings.get(
            'cache/in_session', type=bool, default=False,
        )

        self.progress = QProgressDialog()
        if self.silent:
            self.progress.setCancelButton(None)
        else:
            self.progress.setCancelButtonText("Cancel")
        self.progress.setWindowFlags(
            Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint,
        )
        self.progress.setAutoClose(False)
        self.progress.setAutoReset(False)
        self.progress.setModal(1)
        self.progress.setWindowTitle(f"Updating {self.featured_mod.upper()}")

    def run(self, *args, **kwargs):
        clearLog()
        log("Update started at " + timestamp())
        log("Using appdata: " + util.APPDATA_DIR)

        self.progress.show()
        QApplication.processEvents()

        # Actual network code adapted from previous version
        self.progress.setLabelText("Connecting to update server...")

        if not self.progress.wasCanceled():
            log("Connected to update server at {}".format(timestamp()))

            self.do_update()

            self.progress.setLabelText("Cleaning up.")

            self.progress.close()
        else:
            log("Cancelled connecting to server.")
            self.result = UpdaterResult.CANCEL

        log("Update finished at {}".format(timestamp()))
        return self.result

    def get_files_to_update(self, mod_id: str, version: str) -> list[dict]:
        return FeaturedModFilesApiConnector(mod_id, version).get_files()

    def get_featured_mod_by_name(self, technical_name: str) -> FeaturedMod:
        return FeaturedModApiConnector().request_and_get_fmod_by_name(technical_name)

    def request_sim_url_by_uid(self, uid: str) -> str:
        return SimModFiles().request_and_get_sim_mod_url_by_id(uid)

    @staticmethod
    def _file_needs_update(file: FeaturedModFile, md5s: dict[str, str]) -> bool:
        incoming_md5 = file.md5
        current_md5 = md5s[file.md5]
        return file.name != Settings.get("game/exe-name") and current_md5 != incoming_md5

    def _calc_md5s(self, files: list[FeaturedModFile]) -> dict[str, str]:
        self.progress.setMaximum(len(files))

        result = {}
        for index, file in enumerate(files, start=1):

            if self.progress.wasCanceled():
                raise UpdaterCancellation()

            filepath = os.path.join(util.APPDATA_DIR, file.group, file.name)

            self.progress.setLabelText(f"Calculating md5 for {file.name}...")

            result[file.md5] = util.md5(filepath)

            self.progress.setValue(index)
        self.progress.setMaximum(0)
        return result

    def fetch_files(self, files: list[FeaturedModFile]) -> None:
        for file in files:
            self.fetch_single_file(file)

    def fetch_single_file(self, file: FeaturedModFile) -> None:
        target_dir = os.path.join(util.APPDATA_DIR, file.group)

        url = file.cacheable_url
        logger.info(f"Updater: Downloading {url}")

        downloaded = download_file(
            url=url,
            target_dir=target_dir,
            name=file.name,
            category="Update",
            silent=False,
            request_params={file.hmac_parameter: file.hmac_token},
            label=f"Downloading FA file : <a href='{url}'>{url}</a><p> ",
        )

        if not downloaded:
            # FIXME: the information about the reason is already given in the
            # dowloadFile function, need to come up with better way probably
            raise UpdaterCancellation(
                "Operation aborted while waiting for data.",
            )

    def move_many_from_cache(self, files: list[FeaturedModFile]) -> None:
        for file in files:
            self.move_from_cache(file)

    def move_from_cache(self, file: FeaturedModFile) -> None:
        src_dir = os.path.join(util.APPDATA_DIR, file.group)
        cache_dir = os.path.join(util.GAME_CACHE_DIR, file.group)
        if os.path.exists(os.path.join(cache_dir, file.md5)):
            shutil.move(
                os.path.join(cache_dir, file.md5),
                os.path.join(src_dir, file.name),
            )

    def move_many_to_cache(self, files: list[dict]) -> None:
        for file in files:
            self.move_to_cache(file)

    def move_to_cache(self, file: FeaturedModFile) -> None:
        src_dir = os.path.join(util.APPDATA_DIR, file.group)
        cache_dir = os.path.join(util.GAME_CACHE_DIR, file.group)
        if os.path.exists(os.path.join(src_dir, file.name)):
            md5 = util.md5(os.path.join(src_dir, file.name))
            shutil.move(
                os.path.join(src_dir, file.name),
                os.path.join(cache_dir, md5),
            )
            util.setAccessTime(os.path.join(cache_dir, md5))

    def replace_from_cache(self, file: FeaturedModFile) -> None:
        self.move_to_cache(file)
        self.move_from_cache(file)

    def replace_many_from_cache(self, files: list[FeaturedModFile]) -> None:
        for file in files:
            self.replace_from_cache(file)

    def check_cache(self, files_to_check: list[FeaturedModFile]) -> None:
        replaceable_files, need_to_download = [], []
        for file in files_to_check:
            cache_dir = os.path.join(util.GAME_CACHE_DIR, file.group)
            os.makedirs(cache_dir, exist_ok=True)
            if self._is_cached(file):
                replaceable_files.append(file)
            else:
                need_to_download.append(file)
        return replaceable_files, need_to_download

    @staticmethod
    def _is_cached(file: FeaturedModFile) -> bool:
        cached_file = os.path.join(util.GAME_CACHE_DIR, file.group, file.name)
        return os.path.isfile(cached_file)

    def create_cache_subdirs(self, files: list[FeaturedModFile]) -> None:
        for file in files:
            target = os.path.join(util.GAME_CACHE_DIR, file.group)
            os.makedirs(target, exist_ok=True)

    def update_files(self, files: list[FeaturedModFile]) -> None:
        """
        Updates the files in the destination
        subdirectory of the Forged Alliance path.
        """
        self.create_cache_subdirs(files)
        self.patch_fa_exe_if_needed(files)
        md5s = self._calc_md5s(files)

        self.progress.setLabelText("Updating files...")

        to_update = list(filter(partial(self._file_needs_update, md5s=md5s), files))
        replacable_files, need_to_download = self.check_cache(to_update)

        if self.keep_cache or self.in_session_cache:
            self.replace_many_from_cache(replacable_files)
            self.move_many_to_cache(need_to_download)
        else:
            self.move_many_from_cache(replacable_files)

        self.fetch_files(need_to_download)

        unpack_movies_and_sounds(files)
        log("Updates applied successfully.")

    def prepare_bin_FAF(self) -> None:
        """
        Creates all necessary files in the binFAF folder, which contains
        a modified copy of all that is in the standard bin folder of
        Forged Alliance
        """
        self.progress.setLabelText("Preparing binFAF...")

        # now we check if we've got a binFAF folder
        FABindir = os.path.join(Settings.get("ForgedAlliance/app/path"), "bin")
        FAFdir = util.BIN_DIR

        # Try to copy without overwriting, but fill in any missing files,
        # otherwise it might miss some files to update
        root_src_dir = FABindir
        root_dst_dir = FAFdir

        for src_dir, _, files in os.walk(root_src_dir):
            dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
            if not os.path.exists(dst_dir):
                os.mkdir(dst_dir)
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if not os.path.exists(dst_file):
                    shutil.copy(src_file, dst_dir)
                st = os.stat(dst_file)
                # make all files we were considering writable, because we may
                # need to patch them
                os.chmod(dst_file, st.st_mode | stat.S_IWRITE)

        self.download_fa_executable()

    def download_fa_executable(self) -> bool:
        fa_exe_name = Settings.get("game/exe-name")
        fa_exe = os.path.join(util.BIN_DIR, fa_exe_name)

        if os.path.isfile(fa_exe):
            return True

        url = Settings.get("game/exe-url")
        return download_file(
            url=url,
            target_dir=util.BIN_DIR,
            name=fa_exe_name,
            category="Update",
            silent=False,
            label=f"Downloading FA file : <a href='{url}'>{url}</a><p>",
        )

    def patch_fa_executable(self, version: int) -> None:
        exe_path = os.path.join(util.BIN_DIR, Settings.get("game/exe-name"))
        version_addresses = (0xd3d40, 0x47612d, 0x476666)
        with open(exe_path, "rb+") as file:
            for address in version_addresses:
                file.seek(address)
                file.write(version.to_bytes(4, "little"))

    def patch_fa_exe_if_needed(self, files: list[FeaturedModFile]) -> None:
        for file in files:
            if file.name == Settings.get("game/exe-name"):
                version = int(self._resolve_base_version(file))
                self.patch_fa_executable(version)
                return

    def update_featured_mod(self, modname: str, modversion: str) -> list[FeaturedModFile]:
        fmod = self.get_featured_mod_by_name(modname)
        files = self.get_files_to_update(fmod.uid, modversion)
        self.update_files(files)
        return files

    def _resolve_modversion(self) -> str:
        if self.modversions:
            return str(max(self.modversions.values()))
        return "latest"

    def _resolve_base_version(self, exe_info: FeaturedModFile | None = None) -> str:
        if self.version:
            return str(self.version)
        if exe_info:
            return str(exe_info.version)
        return "latest"

    def do_update(self) -> None:
        """ The core function that does most of the actual update work."""
        try:
            if self.sim_mod:
                uid, name = self.sim_mod
                if utils.downloadMod(self.request_sim_url_by_uid(uid), name):
                    self.result = UpdaterResult.SUCCESS
                else:
                    self.result = UpdaterResult.FAILURE
            else:
                # Prepare FAF directory & all necessary files
                self.prepare_bin_FAF()
                # Update the mod if it's requested
                if self.featured_mod in ("faf", "fafbeta", "fafdevelop", "ladder1v1"):
                    self.update_featured_mod(self.featured_mod, self._resolve_base_version())
                else:
                    # update faf first
                    self.update_featured_mod("faf", self._resolve_base_version())
                    # update featured mod then
                    self.update_featured_mod(self.featured_mod, self._resolve_modversion())
        except UpdaterCancellation as e:
            log("CANCELLED: {}".format(e))
            self.result = UpdaterResult.CANCEL
        except BaseException as e:
            log("EXCEPTION: {}".format(e))
            self.result = UpdaterResult.FAILURE
        else:
            self.result = UpdaterResult.SUCCESS

        # Integrated handlers for the various things that could go wrong
        if self.result == UpdaterResult.CANCEL:
            pass  # The user knows damn well what happened here.
        elif self.result == UpdaterResult.PASS:
            QMessageBox.information(
                QApplication.activeWindow(),
                "Installation Required",
                "You can't play without a legal version of Forged Alliance.",
            )
        elif self.result == UpdaterResult.BUSY:
            QMessageBox.information(
                QApplication.activeWindow(),
                "Server Busy",
                (
                    "The Server is busy preparing new patch files.<br/>Try "
                    "again later."
                ),
            )
        elif self.result == UpdaterResult.FAILURE:
            failureDialog()

        # If nothing terribly bad happened until now,
        # the operation is a success and/or the client can display what's up.
        return self.result


def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# This is a pretty rough port of the old installer wizard. It works, but will
# need some work later
def failureDialog():
    """
    The dialog that shows the user the log if something went wrong.
    """
    raise Exception(dumpPlainText())
