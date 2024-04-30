import binascii
import logging
import os
import zipfile

from util import APPDATA_DIR

logger = logging.getLogger(__name__)


def crc32(filepath: str) -> int | None:
    try:
        with open(filepath) as stream:
            return binascii.crc32(stream.read())
    except Exception as e:
        logger.exception(f"CRC check fail! Details: {e}")
        return None


def unpack_movies(files: list[dict]) -> None:
    """
    Unpacks movies (based on path in zipfile) to the movies folder.
    Movies must be unpacked for FA to be able to play them.
    This is a hack needed because the game updater can only handle bin and
    gamedata.
    """

    logger.info(f"checking updated files: {files}")

    # construct dirs
    gd = os.path.join(APPDATA_DIR, "gamedata")

    for file in files:
        fname = file["name"]
        origpath = os.path.join(gd, fname)

        if os.path.exists(origpath) and zipfile.is_zipfile(origpath):
            try:
                zf = zipfile.ZipFile(origpath)
            except Exception as e:
                logger.exception(f"Failed to open Game File {origpath!r}: {e}")
                continue

            for zi in zf.infolist():
                if zi.filename.startswith("movies"):
                    tgtpath = os.path.join(APPDATA_DIR, zi.filename)
                    # copy only if file is different - check first if file
                    # exists, then if size is changed, then crc
                    if (
                        not os.path.exists(tgtpath)
                        or os.stat(tgtpath).st_size != zi.file_size
                        or crc32(tgtpath) != zi.CRC
                    ):
                        zf.extract(zi, APPDATA_DIR)
