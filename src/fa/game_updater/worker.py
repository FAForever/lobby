from __future__ import annotations

import logging
import os
import shutil
import stat
from functools import wraps

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
from fa.game_updater.misc import ProgressInfo
from fa.game_updater.misc import UpdaterCancellation
from fa.game_updater.misc import UpdaterFailure
from fa.game_updater.misc import UpdaterResult
from fa.game_updater.misc import log
from fa.game_updater.patcher import FAPatcher
from fa.utils import unpack_movies_and_sounds

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

        self.dlers: list[FileDownload] = []
        self._interruption_requested = False
        self.fa_patcher = FAPatcher()

    def _check_interruption(fn):
        @wraps(fn)
        def wrapper(self, *args, **kwargs):
            if self._interruption_requested:
                raise UpdaterCancellation("User aborted the update")
            return fn(self, *args, **kwargs)
        return wrapper

    def get_files_to_update(self, mod_id: str, version: str) -> list[dict]:
        return FeaturedModFilesApiConnector(mod_id, version).get_files()

    def get_featured_mod_by_name(self, technical_name: str) -> FeaturedMod:
        return FeaturedModApiConnector().request_and_get_fmod_by_name(technical_name)

    @staticmethod
    def _filter_files_to_update(
        files: list[FeaturedModFile],
        precalculated_md5s: dict[str, str],
    ) -> list[FeaturedModFile]:
        return [file for file in files if precalculated_md5s[file.md5] != file.md5]

    @_check_interruption
    def _calculate_md5s(self, files: list[FeaturedModFile]) -> dict[str, str]:
        total = len(files)
        result = {}
        for index, file in enumerate(files, start=1):
            filepath = os.path.join(util.APPDATA_DIR, file.group, file.name)
            result[file.md5] = util.md5(filepath)
            self.hash_progress.emit(ProgressInfo(index, total, file.name))
        return result

    def fetch_fmod_file(self, file: FeaturedModFile) -> None:
        target_path = os.path.join(util.APPDATA_DIR, file.group, file.name)
        url = file.cacheable_url
        self._download(target_path, url, {file.hmac_parameter: file.hmac_token})

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
        cached_file = os.path.join(util.GAME_CACHE_DIR, file.group, file.md5)
        return os.path.isfile(cached_file)

    def ensure_subdirs(self, files: list[FeaturedModFile]) -> None:
        for file in files:
            cache = os.path.join(util.GAME_CACHE_DIR, file.group)
            os.makedirs(cache, exist_ok=True)
            os.makedirs(util.GAMEDATA_DIR, exist_ok=True)

    @_check_interruption
    def update_file(
            self,
            file: FeaturedModFile,
            precalculated_md5s: dict[str, str] | None = None,
    ) -> None:
        self.move_to_cache(file, precalculated_md5s)
        if self._is_cached(file):
            self.move_from_cache(file)
        else:
            self.fetch_fmod_file(file)

    @_check_interruption
    def update_files(self, files: list[FeaturedModFile]) -> None:
        """
        Updates the files in the destination
        subdirectory of the Forged Alliance path.
        """
        self.ensure_subdirs(files)
        md5s = self._calculate_md5s(files)

        to_update = self._filter_files_to_update(files, md5s)
        total = len(to_update)

        if total == 0:
            self.mod_progress.emit(ProgressInfo(0, 0, ""))

        for index, file in enumerate(to_update, start=1):
            self.update_file(file, md5s)
            self.mod_progress.emit(ProgressInfo(index, total, file.name))

        self.unpack_movies_and_sounds(files)
        self.patch_fa_exe_if_needed(files)

    @_check_interruption
    def unpack_movies_and_sounds(self, files: list[FeaturedModFile]) -> None:
        logger.info("Checking files for movies and sounds")

        total = len(files)
        for index, file in enumerate(files, start=1):
            unpack_movies_and_sounds(file)
            self.extras_progress.emit(ProgressInfo(index, total, file.name))

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
                src_file = os.path.join(src_dir, file)
                dst_file = os.path.join(dst_dir, file)
                if not os.path.exists(dst_file):
                    shutil.copy(src_file, dst_dir)
                st = os.stat(dst_file)
                # make all files we were considering writable, because we may
                # need to patch them
                os.chmod(dst_file, st.st_mode | stat.S_IWRITE)
                self.game_progress.emit(ProgressInfo(index, total_files, file))

    def _download(self, target_path: str, url: str, params: dict) -> None:
        logger.info(f"Updater: Downloading {url}")
        dler = FileDownload(target_path, self.nam, url, params)
        dler.blocksize = None
        dler.progress.connect(self.download_progress.emit)
        dler.start.connect(self.download_started.emit)
        dler.finished.connect(self.download_finished.emit)
        self.dlers.append(dler)
        dler.run()
        dler.waitForCompletion()
        if dler.canceled:
            raise UpdaterCancellation(dler.error_string())
        elif dler.failed():
            raise UpdaterFailure(f"Update failed: {dler.error_sring()}")

    def patch_fa_executable(self, exe_info: FeaturedModFile) -> None:
        exe_path = os.path.join(util.BIN_DIR, exe_info.name)
        version = int(self._resolve_base_version(exe_info))

        if version == self.fa_patcher.read_version(exe_path):
            return

        for attempt in range(10):  # after download antimalware can interfere in our update process
            if self.fa_patcher.patch(exe_path, version):
                return
            logger.warning(f"Could not open fa exe for patching. Attempt #{attempt + 1}")
            self.thread().msleep(500)
        else:
            raise UpdaterFailure("Could not update FA exe to the correct version")

    def patch_fa_exe_if_needed(self, files: list[FeaturedModFile]) -> None:
        for file in files:
            if file.name == Settings.get("game/exe-name"):
                self.patch_fa_executable(file)
                return

    @_check_interruption
    def update_featured_mod(self, modname: str, modversion: str) -> list[FeaturedModFile]:
        fmod = self.get_featured_mod_by_name(modname)
        files = self.get_files_to_update(fmod.xd, modversion)
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
            log(f"CANCELLED: {e}", logger)
            self.result = UpdaterResult.CANCEL
        except Exception as e:
            log(f"EXCEPTION: {e}", logger)
            logger.exception(f"EXCEPTION: {e}")
            self.result = UpdaterResult.FAILURE
        else:
            self.result = UpdaterResult.SUCCESS
        self.done.emit(self.result)

    def abort(self) -> None:
        for dler in self.dlers:
            dler.cancel()
        self._interruption_requested = True
