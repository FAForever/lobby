import logging

# We only want one instance of Forged Alliance to run, so we use a singleton
# here (other modules may wish to connect to its signals so it needs
# persistence)
from . import check
from . import factions
from . import game_updater
from . import maps
from . import mods
from . import replayserver
from . import wizards
from .game_process import instance
from .play import run
from .replay import replay

__all__ = (
    "check",
    "factions",
    "maps",
    "mods",
    "replayserver",
    "game_updater",
    "wizards",
    "instance",
    "run",
    "replay",
)

logger = logging.getLogger(__name__)
