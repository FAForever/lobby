from __future__ import annotations

import logging
import os
import shutil
import stat

from PyQt6.QtCore import QObject
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtNetwork import QNetworkAccessManager

import util
from api.featured_mod_api import FeaturedModApiConnector
from api.featured_mod_api import FeaturedModFilesApiConnector
from api.models.FeaturedMod import FeaturedMod
from api.models.FeaturedModFile import FeaturedModFile
from config import Settings
from downloadManager import FileDownload
from fa.updater_misc import ProgressInfo
from fa.updater_misc import UpdaterCancellation
from fa.updater_misc import UpdaterFailure
from fa.updater_misc import UpdaterResult
from fa.updater_misc import log
from fa.utils import unpack_movies_and_sounds
from vaults.dialogs import download_file

logger = logging.getLogger(__name__)


class UpdaterWorker(QObject):
    done = pyqtSignal(UpdaterResult)

    current_mod = pyqtSignal(ProgressInfo)
    hash_progress = pyqtSignal(ProgressInfo)
    extras_progress = pyqtSignal(ProgressInfo)
    game_progress = pyqtSignal(ProgressInfo)
    mod_progress = pyqtSignal(ProgressInfo)

    download_started = pyqtSignal(FileDownload)
    download_progress = pyqtSignal(FileDownload)
    download_finished = pyqtSignal(FileDownload)

    def __init__(
            self,
            featured_mod: str,
            version: int | None,
            modversions: dict | None,
            silent: bool = False,
    ) -> None:
        super().__init__()
        self.featured_mod = featured_mod
        self.version = version
        self.modversions = modversions
        self.silent = silent

        self.nam = QNetworkAccessManager(self)
        self.result = UpdaterResult.NONE

        keep_cache = not Settings.get("cache/do_not_keep", type=bool, default=True)
        in_session_cache = Settings.get("cache/in_session", type=bool, default=False)
        self.cache_enabled = keep_cache or in_session_cache

    def get_files_to_update(self, mod_id: str, version: str) -> list[dict]:
        return FeaturedModFilesApiConnector(mod_id, version).get_files()

    def get_featured_mod_by_name(self, technical_name: str) -> FeaturedMod:
        return FeaturedModApiConnector().request_and_get_fmod_by_name(technical_name)

    @staticmethod
    def _filter_files_to_update(
        files: list[FeaturedModFile],
        precalculated_md5s: dict[str, str],
    ) -> list[FeaturedModFile]:
        exe_name = Settings.get("game/exe-name")
        return [
            file for file in files
            if precalculated_md5s[file.md5] != file.md5 and file.name != exe_name
        ]

    def _calculate_md5s(self, files: list[FeaturedModFile]) -> dict[str, str]:
        total = len(files)
        result = {}
        for index, file in enumerate(files, start=1):
            filepath = os.path.join(util.APPDATA_DIR, file.group, file.name)
            self.hash_progress.emit(ProgressInfo(index, total, file.name))
            result[file.md5] = util.md5(filepath)
        return result

    def fetch_file(self, file: FeaturedModFile) -> None:
        target_path = os.path.join(util.APPDATA_DIR, file.group, file.name)
        url = file.cacheable_url
        logger.info(f"Updater: Downloading {url}")

        dler = FileDownload(
            target_path=target_path,
            nam=self.nam,
            addr=url,
            request_params={file.hmac_parameter: file.hmac_token},
        )
        dler.progress.connect(lambda: self.download_progress.emit(dler))
        dler.start.connect(lambda: self.download_started.emit(dler))
        dler.finished.connect(lambda: self.download_finished.emit(dler))
        dler.run()
        dler.waitForCompletion()
        if dler.failed():
            raise UpdaterFailure()

    def move_from_cache(self, file: FeaturedModFile) -> None:
        src_dir = os.path.join(util.APPDATA_DIR, file.group)
        cache_dir = os.path.join(util.GAME_CACHE_DIR, file.group)
        if os.path.exists(os.path.join(cache_dir, file.md5)):
            shutil.move(
                os.path.join(cache_dir, file.md5),
                os.path.join(src_dir, file.name),
            )

    def move_to_cache(
            self,
            file: FeaturedModFile,
            precalculated_md5s: dict[str, str] | None = None,
    ) -> None:
        precalculated_md5s = precalculated_md5s or {}
        src_dir = os.path.join(util.APPDATA_DIR, file.group)
        cache_dir = os.path.join(util.GAME_CACHE_DIR, file.group)
        if os.path.exists(os.path.join(src_dir, file.name)):
            md5 = precalculated_md5s.get(file.md5, util.md5(os.path.join(src_dir, file.name)))
            shutil.move(
                os.path.join(src_dir, file.name),
                os.path.join(cache_dir, md5),
            )
            util.setAccessTime(os.path.join(cache_dir, md5))

    @staticmethod
    def _is_cached(file: FeaturedModFile) -> bool:
        cached_file = os.path.join(util.GAME_CACHE_DIR, file.group, file.name)
        return os.path.isfile(cached_file)

    def create_cache_subdirs(self, files: list[FeaturedModFile]) -> None:
        for file in files:
            target = os.path.join(util.GAME_CACHE_DIR, file.group)
            os.makedirs(target, exist_ok=True)

    def update_file(
            self,
            file: FeaturedModFile,
            precalculated_md5s: dict[str, str] | None = None,
    ) -> None:
        if self._is_cached(file):
            if self.cache_enabled:
                self.move_to_cache(file, precalculated_md5s)
            self.move_from_cache(file)
        else:
            self.fetch_file(file)

    def update_files(self, files: list[FeaturedModFile]) -> None:
        """
        Updates the files in the destination
        subdirectory of the Forged Alliance path.
        """
        self.create_cache_subdirs(files)
        self.patch_fa_exe_if_needed(files)
        md5s = self._calculate_md5s(files)

        to_update = self._filter_files_to_update(files, md5s)
        total = len(to_update)

        if total == 0:
            self.mod_progress.emit(ProgressInfo(0, 0, ""))

        for index, file in enumerate(to_update, start=1):
            self.mod_progress.emit(ProgressInfo(index, total, file.name))
            self.update_file(file, md5s)

        self.unpack_movies_and_sounds(files)

    def unpack_movies_and_sounds(self, files: list[FeaturedModFile]) -> None:
        logger.info("Checking files for movies and sounds")

        total = len(files)
        for index, file in enumerate(files, start=1):
            self.extras_progress.emit(ProgressInfo(index, total, file.name))
            unpack_movies_and_sounds(file)

    def prepare_bin_FAF(self) -> None:
        """
        Creates all necessary files in the binFAF folder, which contains
        a modified copy of all that is in the standard bin folder of
        Forged Alliance
        """
        # now we check if we've got a binFAF folder
        FABindir = os.path.join(Settings.get("ForgedAlliance/app/path"), "bin")
        FAFdir = util.BIN_DIR

        # Try to copy without overwriting, but fill in any missing files,
        # otherwise it might miss some files to update
        root_src_dir = FABindir
        root_dst_dir = FAFdir

        for src_dir, _, files in os.walk(root_src_dir):
            dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
            os.makedirs(dst_dir, exist_ok=True)
            total_files = len(files)
            for index, file in enumerate(files, start=1):
                self.game_progress.emit(ProgressInfo(index, total_files, file))
                src_file = os.path.join(src_dir, file)
                dst_file = os.path.join(dst_dir, file)
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
            # Prepare FAF directory & all necessary files
            self.prepare_bin_FAF()
            # Update the mod if it's requested
            if self.featured_mod in ("faf", "fafbeta", "fafdevelop", "ladder1v1"):
                self.current_mod.emit(ProgressInfo(1, 1, self.featured_mod))
                self.update_featured_mod(self.featured_mod, self._resolve_base_version())
            else:
                # update faf first
                self.current_mod.emit(ProgressInfo(1, 2, "FAF"))
                self.update_featured_mod("faf", self._resolve_base_version())
                # update featured mod then
                self.current_mod.emit(ProgressInfo(2, 2, self.featured_mod))
                self.update_featured_mod(self.featured_mod, self._resolve_modversion())
        except UpdaterCancellation as e:
            log("CANCELLED: {}".format(e), logger)
            self.result = UpdaterResult.CANCEL
        except Exception as e:
            log("EXCEPTION: {}".format(e), logger)
            logger.exception(f"EXCEPTION: {e}")
            self.result = UpdaterResult.FAILURE
        else:
            self.result = UpdaterResult.SUCCESS
        self.done.emit(self.result)
