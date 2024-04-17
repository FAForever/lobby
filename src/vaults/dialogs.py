import logging
import os
from typing import Callable

from PyQt6 import QtCore
from PyQt6 import QtNetwork
from PyQt6 import QtWidgets

from downloadManager import FileDownload
from downloadManager import ZipDownloadExtract

logger = logging.getLogger(__name__)


class VaultDownloadDialog(object):
    # Result codes
    SUCCESS = 0
    CANCELED = 1
    DL_ERROR = 2
    UNKNOWN_ERROR = 3

    def __init__(
            self,
            dler: FileDownload | ZipDownloadExtract,
            title: str,
            label: str,
            silent: bool = False,
    ) -> None:
        self._silent = silent
        self._result = None

        self._dler = dler
        self._dler.start.connect(self._start)
        self._dler.progress.connect(self._cont)
        self._dler.finished.connect(self._finished)
        self._dler.blocksize = 8192

        self._progress = QtWidgets.QProgressDialog()
        self._progress.setWindowTitle(title)
        self.label = label
        self._progress.setLabelText(self.label)
        if not self._silent:
            self._progress.setCancelButtonText("Cancel")
        else:
            self._progress.setCancelButton(None)
        self._progress.setWindowFlags(
            QtCore.Qt.WindowType.CustomizeWindowHint | QtCore.Qt.WindowType.WindowTitleHint,
        )
        self._progress.setAutoReset(False)
        self._progress.setModal(1)
        self._progress.canceled.connect(self._dler.cancel)

        progressBar = QtWidgets.QProgressBar(self._progress)
        progressBar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._progress.setBar(progressBar)

        self.progress_measure_interaval = 250
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.progress_measure_interaval)
        self.timer.timeout.connect(self.updateLabel)
        self.bytes_prev = 0

    def updateLabel(self) -> None:
        label_text = f"{self.label}\n\n{self.get_download_progress_mb()}"
        speed_text = f"({self.get_download_speed()} MB/s)"
        if self._dler.bytes_total > 0:
            label_text = f"{label_text}/{self.get_download_size_mb()} MB\n\n{speed_text}"
        else:
            label_text = f"{label_text} MB {speed_text}"
        self._progress.setLabelText(label_text)

    def get_download_speed(self) -> float:
        bytes_diff = self._dler.bytes_progress - self.bytes_prev
        self.bytes_prev = self._dler.bytes_progress
        return round(bytes_diff * (1000 / self.progress_measure_interaval) / 1024 / 1024, 2)

    def get_download_progress_mb(self) -> float:
        return round(self._dler.bytes_progress / 1024 / 1024, 2)

    def get_download_size_mb(self) -> float:
        return round(self._dler.bytes_total / 1024 / 1024, 2)

    def run(self):
        self.updateLabel()
        self.timer.start()
        self._progress.show()
        self._dler.run()
        self._dler.waitForCompletion()
        return self._result

    def _start(self, dler):
        self._progress.setMinimum(0)
        if dler.bytes_total > 0:
            self._progress.setMaximum(dler.bytes_total)
        else:
            self._progress.setMaximum(0)

    def _cont(self, dler):
        if dler.bytes_total > 0:
            self._progress.setValue(dler.bytes_progress)
            self._progress.setMaximum(dler.bytes_total)

        QtWidgets.QApplication.processEvents()

    def _finished(self, dler):
        self.timer.stop()
        self._progress.reset()

        if not dler.succeeded():
            if dler.canceled:
                self._result = self.CANCELED
                return

            elif dler.error:
                self._result = self.DL_ERROR
                return
            else:
                logger.error('Unknown download error')
                self._result = self.UNKNOWN_ERROR
                return

        self._result = self.SUCCESS
        return


# FIXME - one day we'll do it properly
_global_nam = QtNetwork.QNetworkAccessManager()


def downloadVaultAssetNoMsg(
        url: str,
        target_dir: str,
        exist_handler: Callable[[str, str], bool],
        name: str,
        category: str,
        silent: bool,
        request_params: dict | None = None,
        label: str = "",
) -> tuple[bool, Callable[[], None] | None]:
    """
    Download and unpack a zip from the vault, interacting with the user and
    logging things.
    """
    global _global_nam
    msg = None
    msg_title = ""
    msg_text = ""
    capit_cat = f"{category[0].upper()}{category[1:]}"

    if os.path.exists(os.path.join(target_dir, name)):
        proceed = exist_handler(target_dir, name)
        if not proceed:
            return False, msg

    dler = ZipDownloadExtract(target_dir, _global_nam, url, request_params)
    ddialog = VaultDownloadDialog(dler, f"Downloading {category}", label or name, silent)
    result = ddialog.run()

    if result == VaultDownloadDialog.CANCELED:
        logger.warning(f"{capit_cat} Download canceled for: {url}")

    if result in [
        VaultDownloadDialog.DL_ERROR,
        VaultDownloadDialog.UNKNOWN_ERROR,
    ]:
        logger.warning(f"Vault download failed, {category} probably not in vault (or broken).")
        msg_title = "{} not downloadable".format(capit_cat)
        msg_text = (
            f"<b>This {category} was not found in the vault (or is broken).</b>"
            f"<br/>You need to get it from somewhere else in order to "
            f"use it."
        )

        def msg():
            QtWidgets.QMessageBox.information(None, msg_title, msg_text)

    if result != VaultDownloadDialog.SUCCESS:
        return False, msg

    return True, msg


def downloadVaultAsset(url, target_dir, exist_handler, name, category, silent):
    ret, dialog = downloadVaultAssetNoMsg(
        url, target_dir, exist_handler, name, category, silent,
    )
    if dialog is not None:
        dialog()

    return ret


def download_file(
        url: str,
        target_dir: str,
        name: str,
        category: str,
        silent: bool,
        request_params: dict | None = None,
        label: str = "",
) -> bool:
    """
    Basically a copy of downloadVaultAssetNoMsg without zip
    """

    global _global_nam
    capit_cat = f"{category[0].upper()}{category[1:]}"

    os.makedirs(target_dir, exist_ok=True)

    target_path = os.path.join(target_dir, name)
    dler = FileDownload(target_path, _global_nam, url, request_params)
    ddialog = VaultDownloadDialog(dler, f"Downloading {category}", label or name, silent)
    result = ddialog.run()

    if result == VaultDownloadDialog.CANCELED:
        logger.warning(f"{capit_cat} Download canceled for: {url}")
    if result in [
        VaultDownloadDialog.DL_ERROR,
        VaultDownloadDialog.UNKNOWN_ERROR,
    ]:
        logger.warning(f"Download failed. {url}")
        QtWidgets.QMessageBox.information(
            None,
            f"{capit_cat} not downloadable",
            f"<b>Failed to download {category} from</b><br/>{url}",
        )

    if result != VaultDownloadDialog.SUCCESS:
        return False

    return True
