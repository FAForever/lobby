import logging
import time
from enum import Enum
from typing import NamedTuple

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QMessageBox


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


class ProgressInfo(NamedTuple):
    progress: int
    total: int
    description: str = ""


# This contains a complete dump of everything that was supplied to logOutput
debug_log = []


def clear_log() -> None:
    global debug_log
    debug_log = []


def log(string: str, loger: logging.Logger) -> None:
    loger.debug(string)
    debug_log.append(str(string))


def dump_plain_text() -> str:
    return "\n".join(debug_log)


def dump_HTML() -> str:
    return "<br/>".join(debug_log)


def timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


# It works, but will need some work later
def failure_dialog() -> None:
    """
    The dialog that shows the user the log if something went wrong.
    """
    mbox = QMessageBox()
    mbox.setParent(QApplication.activeWindow())
    mbox.setWindowFlags(Qt.WindowType.Dialog)
    mbox.setWindowTitle("Update Failed")
    mbox.setText("An error occurred during downloading/copying/moving files")
    mbox.setDetailedText(dump_plain_text())
    mbox.exec()
