"""
Settings for notifications: If a game is full
"""
import src.notifications as ns
from src.notifications.ns_hook import NsHook


class NsHookGameFull(NsHook):
    def __init__(self):
        NsHook.__init__(self, ns.Notifications.GAME_FULL)
