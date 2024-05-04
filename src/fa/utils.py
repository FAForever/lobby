import binascii
import logging
import os
import zipfile

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QProgressDialog

from api.models.FeaturedModFile import FeaturedModFile
from util import APPDATA_DIR

logger = logging.getLogger(__name__)


def crc32(filepath: str) -> int | None:
    try:
        with open(filepath, "rb") as stream:
            return binascii.crc32(stream.read())
    except Exception as e:
        logger.exception(f"CRC check for {filepath!r} fail! Details: {e}")
        return None


def unpack_movies_and_sounds_from_file(file: FeaturedModFile) -> None:
    """
    Unpacks movies and sounds (based on path in zipfile) to the corresponding
    folder. Movies must be unpacked for FA to be able to play them.
    This is a hack needed because the game updater can only handle bin and
    gamedata.
    """
    # construct dirs
    gd = os.path.join(APPDATA_DIR, "gamedata")

    origpath = os.path.join(gd, file.name)

    if os.path.exists(origpath) and zipfile.is_zipfile(origpath):
        try:
            zf = zipfile.ZipFile(origpath)
        except Exception as e:
            logger.exception(f"Failed to open Game File {origpath!r}: {e}")
            return

        for zi in zf.infolist():
            movie_or_sound = (
                zi.filename.startswith("movies")
                or zi.filename.startswith("sounds")
            )
            if movie_or_sound and not zi.is_dir():
                tgtpath = os.path.join(APPDATA_DIR, zi.filename)
                # copy only if file is different - check first if file
                # exists, then if size is changed, then crc
                if (
                    not os.path.exists(tgtpath)
                    or os.stat(tgtpath).st_size != zi.file_size
                    or crc32(tgtpath) != zi.CRC
                ):
                    zf.extract(zi, APPDATA_DIR)


def unpack_movies_and_sounds(files: list[FeaturedModFile]) -> None:
    logger.info("Checking files for movies and sounds")

    progress = QProgressDialog()
    progress.setWindowTitle("Updating Movies and Sounds")
    progress.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
    progress.setModal(True)
    progress.setCancelButton(None)
    progress.setMaximum(len(files))
    progress.setValue(0)

    for index, file in enumerate(files, start=1):
        progress.setLabelText(f"Checking for movies and sounds in {file.name}...")
        unpack_movies_and_sounds_from_file(file)
        progress.setValue(index)
