from __future__ import annotations

import random
from typing import Any

from PyQt6.QtWidgets import QComboBox
from PyQt6.QtWidgets import QSpinBox

import config


class OptionMixin:
    def reset(self) -> None:
        raise NotImplementedError

    def set_value(self, value: Any) -> None:
        raise NotImplementedError

    def value(self) -> Any:
        raise NotImplementedError

    def active(self) -> bool:
        raise NotImplementedError

    def load(self) -> None:
        raise NotImplementedError

    def save(self) -> None:
        raise NotImplementedError

    def as_cmd_arg(self) -> list[str]:
        raise NotImplementedError


class MapGenOption(OptionMixin):
    def __init__(
            self,
            name: str,
            ui_elem: QComboBox | QSpinBox,
            typ: type = str,
            default: Any = None,
    ) -> None:
        self.conf = config.Settings()
        self.name = name
        self.ui_elem = ui_elem
        self.typ = typ
        self.default = default

    def reset(self) -> None:
        if self.default is not None:
            self.set_value(self.default)

    def load(self) -> None:
        self.set_value(
            self.conf.get(
                f"mapGenerator/{self.ui_elem.objectName()}",
                default=self.default,
                type=self.typ,
            ),
        )

    def save(self) -> None:
        self.conf.set(
            f"mapGenerator/{self.ui_elem.objectName()}",
            self.value(),
        )

    def as_cmd_arg(self) -> list[str]:
        return [f"--{self.name}", str(self.value())]


class ComboBoxOption(MapGenOption):
    def __init__(
            self,
            name: str,
            ui_elem: QComboBox,
            default: str | None = None,
            opts: list[str] | None = None,
    ) -> None:
        MapGenOption.__init__(self, name, ui_elem, str, default)
        self.opts = opts

    def set_value(self, value: str) -> None:
        self.ui_elem.setCurrentText(value)

    def value(self) -> str:
        return self.ui_elem.currentText()

    def active(self) -> bool:
        return self.ui_elem.isEnabled() and self.value() != self.default

    def populate(self) -> None:
        if self.opts is None:
            return
        for opt in self.opts:
            self.ui_elem.addItem(opt)

    def load(self) -> None:
        self.populate()
        MapGenOption.load(self)


class SpinBoxOption(MapGenOption):
    def __init__(
            self,
            name: str,
            ui_elem: QSpinBox,
            typ: type,
            default: int | float | None = None,
    ) -> None:
        MapGenOption.__init__(self, name, ui_elem, typ, default)

    def set_value(self, value: int | float) -> None:
        self.ui_elem.setValue(value)

    def value(self) -> int | float:
        return self.ui_elem.value()

    def active(self) -> bool:
        return self.ui_elem.isEnabled()


class RangeOption(OptionMixin):
    def __init__(
            self,
            name: str,
            minimum: SpinBoxOption,
            maximum: SpinBoxOption,
    ) -> None:
        self.name = name
        self.minimum = minimum
        self.maximum = maximum

    def reset(self) -> None:
        self.minimum.reset()
        self.maximum.reset()

    def value(self) -> float:
        minval = min(self.minimum.value(), self.maximum.value())
        maxval = max(self.minimum.value(), self.maximum.value())
        return random.randrange(round(minval), round(maxval + 1)) / 100

    def active(self) -> bool:
        return self.minimum.active() and self.maximum.active()

    def load(self) -> None:
        self.minimum.load()
        self.maximum.load()

    def save(self) -> None:
        self.minimum.save()
        self.maximum.save()

    def as_cmd_arg(self) -> list[str]:
        return [f"--{self.name}", str(self.value())]
