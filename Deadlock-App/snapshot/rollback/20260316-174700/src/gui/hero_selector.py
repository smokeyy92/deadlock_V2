from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QLineEdit, QVBoxLayout, QWidget

_HEROES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "heroes.json"


class HeroSelector(QWidget):
    hero_selected = Signal(str)

    def __init__(self, label: str = "Hero", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = label
        self._all_heroes: list[str] = []
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.search = QLineEdit()
        self.search.setPlaceholderText(f"Search {self._label}…")
        self.combo = QComboBox()
        self.combo.setMinimumWidth(180)

        layout.addWidget(self.search)
        layout.addWidget(self.combo)

        self.search.textChanged.connect(self._filter)
        self.combo.currentTextChanged.connect(self._on_changed)

    def reload(self) -> None:
        self._all_heroes = []
        if _HEROES_PATH.exists():
            try:
                data = json.loads(_HEROES_PATH.read_text(encoding="utf-8"))
                self._all_heroes = sorted(
                    h.get("name", "") for h in data if isinstance(h, dict) and h.get("name")
                )
            except Exception:
                pass
        self._rebuild_combo(self._all_heroes)

    def _rebuild_combo(self, names: list[str]) -> None:
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItem(f"-- {self._label} --")
        for name in names:
            self.combo.addItem(name)
        self.combo.blockSignals(False)

    def _filter(self, text: str) -> None:
        filtered = [h for h in self._all_heroes if text.lower() in h.lower()] if text else self._all_heroes
        self._rebuild_combo(filtered)

    def _on_changed(self, text: str) -> None:
        if not text.startswith("--"):
            self.hero_selected.emit(text)

    def get_selected(self) -> str:
        val = self.combo.currentText()
        return "" if val.startswith("--") else val

    def clear_selection(self) -> None:
        self.combo.setCurrentIndex(0)
