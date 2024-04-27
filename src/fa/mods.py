import logging

from PyQt6 import QtWidgets

import config
import fa
from vaults.modvault.utils import getInstalledMods
from vaults.modvault.utils import setActiveMods

logger = logging.getLogger(__name__)


def checkMods(mods: dict[str, str]) -> bool:  # mods is a dictionary of uid-name pairs
    """
    Assures that the specified mods are available in FA, or returns False.
    Also sets the correct active mods in the ingame mod manager.
    """
    logger.info("Updating FA for mods {}".format(", ".join(mods)))

    inst = set(mod.uid for mod in getInstalledMods())
    to_download = {uid: name for uid, name in mods.items() if uid not in inst}

    auto = config.Settings.get('mods/autodownload', default=False, type=bool)
    if not auto:
        mod_names = ", ".join(mods.values())
        msgbox = QtWidgets.QMessageBox()
        msgbox.setWindowTitle("Download Mod")
        msgbox.setText(
            "Seems that you don't have mods used in this game. Do "
            "you want to download them?<br/><b>{}</b>".format(mod_names),
        )
        msgbox.setInformativeText(
            "If you respond 'Yes to All' mods will be "
            "downloaded automatically in the future",
        )
        msgbox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.YesToAll
            | QtWidgets.QMessageBox.StandardButton.No,
        )
        result = msgbox.exec()
        if result == QtWidgets.QMessageBox.StandardButton.No:
            return False
        elif result == QtWidgets.QMessageBox.StandardButton.YesToAll:
            config.Settings.set('mods/autodownload', True)

    for item in to_download.items():
        # Spawn an update for the required mod
        updater = fa.updater.Updater("sim", sim_mod=item)
        result = updater.run()
        if result != fa.updater.UpdaterResult.SUCCESS:
            logger.warning(f"Failure getting {item}")
            return False

    actual_mods = []
    uids = {mod.uid: mod for mod in getInstalledMods()}
    for uid, name in mods.items():
        if uid not in uids:
            QtWidgets.QMessageBox.warning(
                None,
                "Mod not Found",
                f"{name} was apparently not installed correctly. Please check this.",
            )
            return
        actual_mods.append(uids[uid])
    if not setActiveMods(actual_mods):
        logger.warning("Couldn't set the active mods in the game.prefs file")
        return False

    return True
