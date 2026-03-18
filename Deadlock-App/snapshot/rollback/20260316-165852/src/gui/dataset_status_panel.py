from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

_SNAPSHOT_PATH = Path(__file__).resolve().parent.parent.parent / "snapshot" / "state.json"
_DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"

_FILE_CHECKS: list[tuple[str, Path]] = [
    ("Heroes processed", _DATA_ROOT / "processed" / "heroes.json"),
    ("Matches processed", _DATA_ROOT / "processed" / "matches.json"),
    ("Synergy matrix", _DATA_ROOT / "analysis" / "synergy_matrix.csv"),
    ("Counter matrix", _DATA_ROOT / "analysis" / "counter_matrix.csv"),
    ("Hero vs Hero matrix", _DATA_ROOT / "analysis" / "hero_vs_hero_matrix.csv"),
    ("Meta scores", _DATA_ROOT / "meta" / "hero_meta_scores.csv"),
    ("Excel export", _DATA_ROOT / "exports" / "deadlock_dataset.xlsx"),
]


class DatasetStatusPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Dataset Status", parent)
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        self._inner_layout = QVBoxLayout(inner)
        scroll.setWidget(inner)
        layout.addWidget(scroll)

        btn = QPushButton("↺ Refresh")
        btn.clicked.connect(self.refresh)
        layout.addWidget(btn)

        self.refresh()

    def refresh(self) -> None:
        while self._inner_layout.count():
            item = self._inner_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        state: dict = {}
        if _SNAPSHOT_PATH.exists():
            try:
                state = json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass

        rows = [
            ("Version", state.get("version", "?")),
            ("Heroes", state.get("hero_count", 0)),
            ("Abilities", state.get("ability_count", 0)),
            ("Items", state.get("item_count", 0)),
            ("Matches", state.get("match_count", 0)),
            ("Last patch", state.get("last_patch_detected") or "unknown"),
            (
                "Last run",
                (state.get("dataset_last_generated") or "never")[:19].replace("T", " "),
            ),
        ]
        for key, val in rows:
            lbl = QLabel(f"<b>{key}:</b> {val}")
            self._inner_layout.addWidget(lbl)

        self._inner_layout.addWidget(QLabel(""))
        self._inner_layout.addWidget(QLabel("<b>Output files:</b>"))
        for name, path in _FILE_CHECKS:
            exists = path.exists()
            color = "#2ecc71" if exists else "#e74c3c"
            status = "✔" if exists else "✘"
            lbl = QLabel(f"<span style='color:{color}'>{status}</span> {name}")
            self._inner_layout.addWidget(lbl)

        self._inner_layout.addStretch()
