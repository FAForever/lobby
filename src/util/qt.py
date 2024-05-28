import types
from contextlib import contextmanager
from typing import Generator

from PyQt6.QtCore import QFile


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
