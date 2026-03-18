from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

_METADATA_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "hero_metadata.json"

_ROLES: list[tuple[str, str]] = [
    ("Hypercarry", "#e74c3c"),
    ("Offcarry", "#e67e22"),
    ("Frontliner/Tank", "#4a90d9"),
    ("Support", "#2ecc71"),
    ("Spirit/Flex/Hybrid", "#9b59b6"),
    ("Pick/Initiator/Catch", "#f39c12"),
]

_ROLE_KEYWORDS: dict[str, str] = {
    "hypercarry": "Hypercarry",
    "offcarry": "Offcarry",
    "frontliner": "Frontliner/Tank",
    "support": "Support",
    "spirit": "Spirit/Flex/Hybrid",
    "initiator": "Pick/Initiator/Catch",
    # anything not recognised (e.g. "unknown") falls back to Spirit/Flex/Hybrid in _TeamBox.update()
}


def _to_slug(name: str) -> str:
    import re
    s = name.lower().replace("&", "and").replace("'", "").replace("-", "_")
    return re.sub(r"\s+", "_", s.strip())


class _TeamBox(QGroupBox):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        layout = QVBoxLayout(self)
        self._bars: dict[str, QProgressBar] = {}
        self._role_heroes: dict[str, QLabel] = {}

        for role, color in _ROLES:
            row = QHBoxLayout()
            lbl = QLabel(role)
            lbl.setMinimumWidth(72)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"QProgressBar::chunk {{ background: {color}; }}")
            row.addWidget(lbl)
            row.addWidget(bar)
            layout.addLayout(row)
            self._bars[role] = bar

            role_heroes = QLabel(f"{role}: none")
            role_heroes.setWordWrap(True)
            layout.addWidget(role_heroes)
            self._role_heroes[role] = role_heroes

        self._strength_lbl = QLabel("Strength: 0 / 100")
        layout.addWidget(self._strength_lbl)

    def update(self, heroes: list[str], metadata: dict) -> None:
        counts: dict[str, int] = {r: 0 for r, _ in _ROLES}
        role_lists: dict[str, list[str]] = {r: [] for r, _ in _ROLES}
        for hero in heroes:
            slug = _to_slug(hero)
            role_raw = metadata.get(slug, {}).get("role", "").lower()
            # Unknown/unmapped roles fall back to Spirit/Flex/Hybrid so heroes are never dropped
            mapped = _ROLE_KEYWORDS.get(role_raw, "Spirit/Flex/Hybrid")
            counts[mapped] += 1
            role_lists[mapped].append(hero)

        max_count = max(counts.values(), default=1) or 1
        for role, bar in self._bars.items():
            bar.setValue(int(counts[role] / max_count * 100))
            heroes_text = ", ".join(role_lists[role]) if role_lists[role] else "none"
            self._role_heroes[role].setText(f"{role}: {heroes_text}")

        filled = sum(1 for v in counts.values() if v > 0)
        diversity = filled / len(_ROLES)
        strength = int(diversity * 100)
        total = sum(counts.values())
        self._strength_lbl.setText(f"Strength: {strength} / 100  ({total} heroes)")


class TeamAnalysisPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Team Analysis", parent)
        layout = QHBoxLayout(self)
        self._meta: dict = {}
        self._team_a = _TeamBox("Team A")
        self._team_b = _TeamBox("Team B")
        layout.addWidget(self._team_a)
        layout.addWidget(self._team_b)

        pred_box = QVBoxLayout()
        self._prediction_title = QLabel("<b>Draft Win Prediction</b>")
        self._prediction_label = QLabel("Complete draft to compute win%")
        self._prediction_label.setWordWrap(True)
        pred_box.addWidget(self._prediction_title)
        pred_box.addWidget(self._prediction_label)
        pred_box.addStretch()
        layout.addLayout(pred_box)
        self._load_metadata()

    def _load_metadata(self) -> None:
        if _METADATA_PATH.exists():
            try:
                self._meta = json.loads(_METADATA_PATH.read_text(encoding="utf-8"))
            except Exception:
                self._meta = {}

    def update_teams(self, team_a: list[str], team_b: list[str]) -> None:
        self._load_metadata()
        self._team_a.update(team_a, self._meta)
        self._team_b.update(team_b, self._meta)

    def set_win_prediction(self, team_a_win_pct: float | None, sample_size: int = 0, source: str = "") -> None:
        if team_a_win_pct is None:
            self._prediction_label.setText("Complete draft to compute win%")
            return

        pct_text = f"{team_a_win_pct:.1f}%"
        if source:
            self._prediction_label.setText(f"{pct_text} chance for Team A ({source}, n={sample_size})")
        else:
            self._prediction_label.setText(f"{pct_text} chance for Team A")
