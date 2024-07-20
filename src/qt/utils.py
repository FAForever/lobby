import types
from contextlib import contextmanager
from typing import Generator

from PyQt6.QtCore import QFile
from PyQt6.QtGui import QPainter


def monkeypatch_method(obj, name, fn):
    old_fn = getattr(obj, name)

    def wrapper(self, *args, **kwargs):
        return fn(self, old_fn, *args, **kwargs)
    setattr(obj, name, types.MethodType(wrapper, obj))


@contextmanager
def qopen(path: str, flags: QFile.OpenModeFlag) -> Generator[QFile, None, None]:
    try:
        file = QFile(path)
        file.open(flags)
        yield file
    finally:
        file.close()


@contextmanager
def qpainter(painter: QPainter) -> Generator[QPainter, None, None]:
    try:
        painter.save()
        yield painter
    finally:
        painter.restore()
