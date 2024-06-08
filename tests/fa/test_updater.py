__author__ = 'Thygrrr'

from typing import Callable

import pytest
from PyQt6 import QtCore
from PyQt6 import QtWidgets

from fa.game_updater.updater import UpdaterProgressDialog


class NoIsFinished(QtCore.QObject):
    finished = QtCore.pyqtSignal()


class NoOpThread(QtCore.QThread):
    def run(self):
        self.yieldCurrentThread()


def test_updater_is_a_dialog(application):
    assert isinstance(UpdaterProgressDialog(None), QtWidgets.QDialog)


def test_updater_has_progress_bar_game_progress(application):
    assert isinstance(
        UpdaterProgressDialog(None).gameProgress,
        QtWidgets.QProgressBar,
    )


def test_updater_has_progress_bar_mod_progress(application):
    assert isinstance(
        UpdaterProgressDialog(None).modProgress,
        QtWidgets.QProgressBar,
    )


def test_updater_has_method_append_log(application):
    assert isinstance(
        UpdaterProgressDialog(None).append_log,
        Callable,
    )


def test_updater_append_log_accepts_string(application):
    UpdaterProgressDialog(None).append_log("Hello Test")


def test_updater_has_method_add_watch(application):
    assert isinstance(
        UpdaterProgressDialog(None).add_watch,
        Callable,
    )


def test_updater_append_log_accepts_qobject_with_signals_finished(application):
    UpdaterProgressDialog(None).add_watch(QtCore.QThread())


def test_updater_add_watch_raises_error_on_watch_without_signal_finished(
    application,
):
    with pytest.raises(AttributeError):
        UpdaterProgressDialog(None).add_watch(QtCore.QObject())


def test_updater_watch_finished_raises_error_on_watch_without_method_finished(
    application,
):
    u = UpdaterProgressDialog(None)
    u.add_watch(NoIsFinished())
    with pytest.raises(AttributeError):
        u.watchFinished()


def test_updater_hides_and_accepts_if_all_watches_are_finished(application):
    u = UpdaterProgressDialog(None)
    t = NoOpThread()

    u.add_watch(t)
    u.show()
    t.start()

    while not t.isFinished():
        pass

    application.processEvents()
    assert not u.isVisible()
    assert u.result() == QtWidgets.QDialog.DialogCode.Accepted


def test_updater_does_not_hide_and_accept_before_all_watches_are_finished(
    application,
):
    u = UpdaterProgressDialog(None)
    t = NoOpThread()
    t_not_finished = QtCore.QThread()

    u.add_watch(t)
    u.add_watch(t_not_finished)
    u.show()
    t.start()

    while not t.isFinished():
        pass

    application.processEvents()
    assert u.isVisible()
    assert not u.result() == QtWidgets.QDialog.DialogCode.Accepted
