from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor
import os

_ANALYSIS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "analysis"

TEAM_A = "Hidden King"
TEAM_B = "Archmother"

TEAM_A_COLOR = "#F39C12"
TEAM_B_COLOR = "#4DA3FF"
PICK_COLOR = "#2ECC71"
BAN_COLOR = "#E74C3C"

TURN_SEQUENCE: list[tuple[str, str]] = [
    (TEAM_A, "BAN"),
    (TEAM_B, "BAN"),
    (TEAM_A, "PICK"),
    (TEAM_B, "PICK"),
    (TEAM_B, "PICK"),
    (TEAM_A, "PICK"),
    (TEAM_A, "PICK"),
    (TEAM_B, "PICK"),
    (TEAM_B, "BAN"),
    (TEAM_A, "BAN"),
    (TEAM_B, "PICK"),
    (TEAM_A, "PICK"),
    (TEAM_A, "PICK"),
    (TEAM_B, "PICK"),
    (TEAM_B, "PICK"),
    (TEAM_A, "PICK"),
]

class HeroCard(QFrame):
    def __init__(self, hero_name, is_ban=False, hero_icon_path=None, border_color="#4a9eff"):
        super().__init__()
        
        # New "Sweet Spot" sizes
        if is_ban:
            # Bans: 70x112
            self.setFixedSize(70, 112)
            self.img_height = 92
            self.name_height = 18
            self.font_size = "8px"
        else:
            # Picks: 95x152
            self.setFixedSize(95, 152)
            self.img_height = 130
            self.name_height = 20
            self.font_size = "9px"

        self.hero_name = hero_name
        accent_color = "#f44336" if is_ban else border_color
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2a2a2a;
                border: 2px solid {accent_color};
                border-radius: 5px;
            }}
            QLabel {{ border: none; background: transparent; color: white; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Hero Portrait
        self.image_label = QLabel()
        self.image_label.setFixedSize(self.width() - 4, self.img_height)
        self.image_label.setScaledContents(True)
        
        if hero_icon_path and os.path.exists(hero_icon_path):
            self.image_label.setPixmap(QPixmap(hero_icon_path))
        else:
            self.image_label.setText("?")
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setStyleSheet(f"font-size: 14px; color: #444;")

        layout.addWidget(self.image_label)

        # Hero Name Label
        self.name_label = QLabel(hero_name.upper())
        self.name_label.setFixedHeight(self.name_height)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet(f"""
            font-size: {self.font_size}; 
            font-weight: bold; 
            background: rgba(0,0,0,0.7);
            border-top: 1px solid {accent_color};
        """)
        layout.addWidget(self.name_label)


class VisualDraftPanel(QWidget):
    def __init__(self, team_name, accent_color):
        super().__init__()
        self.team_name = team_name
        self.accent_color = accent_color
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.setSpacing(15)

        # Team Title (Hidden King / Archmother)
        self.title_label = QLabel(self.team_name.upper())
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"""
            color: {self.accent_color};
            font-size: 28px;
            font-weight: bold;
            letter-spacing: 6px;
        """)
        self.layout.addWidget(self.title_label)

        # PICKS row (Centered)
        self.picks_layout = QHBoxLayout()
        self.picks_layout.setAlignment(Qt.AlignCenter)
        self.picks_layout.setSpacing(12)
        self.layout.addLayout(self.picks_layout)

        # BANS row (Centered, no label)
        self.bans_layout = QHBoxLayout()
        self.bans_layout.setAlignment(Qt.AlignCenter)
        self.bans_layout.setSpacing(12)
        self.layout.addLayout(self.bans_layout)

    def update_draft(self, picks_data, bans_data, get_icon_func):
        self._clear_layout(self.picks_layout)
        self._clear_layout(self.bans_layout)

        # Update Picks with Team Color
        for pick in picks_data:
            path = get_icon_func(pick['name'])
            card = HeroCard(pick['name'], is_ban=False, 
                            hero_icon_path=path, border_color=self.accent_color)
            self.picks_layout.addWidget(card)

        # Update Bans with Red Color
        for ban in bans_data:
            path = get_icon_func(ban['name'])
            card = HeroCard(ban['name'], is_ban=True, 
                            hero_icon_path=path, border_color="#f44336")
            self.bans_layout.addWidget(card)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

class DraftTimelinePanel(QGroupBox):
    draft_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Draft Timeline", parent)
        layout = QVBoxLayout(self)

        legend = QLabel(
            f"<b>Legend:</b> "
            f"<span style='color:{TEAM_A_COLOR}'>Orange = {TEAM_A}</span> | "
            f"<span style='color:{TEAM_B_COLOR}'>Blue = {TEAM_B}</span> | "
            f"<span style='color:{PICK_COLOR}'>Green = Pick</span> | "
            f"<span style='color:{BAN_COLOR}'>Red = Ban</span>"
        )
        legend.setWordWrap(True)
        layout.addWidget(legend)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Step", "Team", "Action"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        self._btn_confirm = QPushButton("Confirm Action")
        self._btn_undo = QPushButton("Undo Last Step")
        self._btn_reset = QPushButton("Reset Draft")
        self._btn_auto = QPushButton("Auto Best Pick")
        for btn in (self._btn_confirm, self._btn_undo, self._btn_reset, self._btn_auto):
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

        self._pending_label = QLabel("Pending: none")
        layout.addWidget(self._pending_label)
        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        self._btn_confirm.clicked.connect(self._confirm)
        self._btn_undo.clicked.connect(self._undo)
        self._btn_reset.clicked.connect(self.reset)
        self._btn_auto.clicked.connect(self._auto_pick)

        self._step: int = 0
        self._history: list[dict[str, str]] = []
        self._pending_hero: str = ""
        self._pending_team: str = TURN_SEQUENCE[0][0]
        self._pending_action: str = TURN_SEQUENCE[0][1]
        self._pending_label.setText(f"Pending: none | Next: Step 1 [{self._pending_team}] {self._pending_action}")
        self._refresh_status_text()

    # ── public API ──────────────────────────────────────────────────────────

    def set_pending(self, hero: str, team: str = TEAM_A, action: str = "PICK") -> bool:
        if self._step >= len(TURN_SEQUENCE):
            self._pending_label.setText("Draft complete. Reset to start a new draft.")
            return False

        if hero in self.get_used_heroes():
            self._pending_label.setText(f"Duplicate hero not allowed: {hero}")
            return False

        expected_team, expected_action = TURN_SEQUENCE[self._step]
        if team != expected_team:
            self._pending_label.setText(
                f"Step {self._step + 1} requires {expected_team} {expected_action}."
            )
            return False

        self._pending_hero = hero
        self._pending_team = expected_team
        self._pending_action = expected_action
        self._pending_label.setText(f"Pending: [{expected_team}]  {expected_action} → {hero}")
        return True

    def get_used_heroes(self) -> set[str]:
        return {entry["hero"] for entry in self._history}

    def get_next_step_text(self) -> str:
        if self._step >= len(TURN_SEQUENCE):
            return "Draft complete"
        team, action = TURN_SEQUENCE[self._step]
        return f"Step {self._step + 1}: {team} {action}"

    def get_team_picks(self, team: str) -> list[str]:
        return [entry["hero"] for entry in self._history if entry["team"] == team and entry["action"] == "PICK"]

    def get_team_bans(self, team: str) -> list[str]:
        return [entry["hero"] for entry in self._history if entry["team"] == team and entry["action"] == "BAN"]

    def is_draft_complete(self) -> bool:
        return self._step >= len(TURN_SEQUENCE)

    def get_status_text(self) -> str:
        hk_picks = self.get_team_picks(TEAM_A)
        hk_bans = self.get_team_bans(TEAM_A)
        am_picks = self.get_team_picks(TEAM_B)
        am_bans = self.get_team_bans(TEAM_B)

        hk_pick_text = ", ".join(hk_picks) if hk_picks else "none"
        hk_ban_text = ", ".join(hk_bans) if hk_bans else "none"
        am_pick_text = ", ".join(am_picks) if am_picks else "none"
        am_ban_text = ", ".join(am_bans) if am_bans else "none"
        return (
            f"<span style='color:{TEAM_A_COLOR}'><b>{TEAM_A}</b></span> "
            f"<span style='color:{PICK_COLOR}'>Picks:</span> {hk_pick_text} | "
            f"<span style='color:{BAN_COLOR}'>Bans:</span> {hk_ban_text}<br>"
            f"<span style='color:{TEAM_B_COLOR}'><b>{TEAM_B}</b></span> "
            f"<span style='color:{PICK_COLOR}'>Picks:</span> {am_pick_text} | "
            f"<span style='color:{BAN_COLOR}'>Bans:</span> {am_ban_text}"
        )

    def _refresh_status_text(self) -> None:
        self._status_label.setText(self.get_status_text())

    def get_team_a_picks(self) -> list[str]:
        return self.get_team_picks(TEAM_A)

    def get_team_b_picks(self) -> list[str]:
        return self.get_team_picks(TEAM_B)

    def reset(self) -> None:
        self._table.setRowCount(0)
        self._step = 0
        self._history.clear()
        self._pending_hero = ""
        next_team, next_action = TURN_SEQUENCE[0]
        self._pending_team = next_team
        self._pending_action = next_action
        self._pending_label.setText(f"Pending: none | Next: Step 1 [{next_team}] {next_action}")
        self._refresh_status_text()
        self.draft_changed.emit()

    # ── private slots ────────────────────────────────────────────────────────

    def _confirm(self) -> None:
        if not self._pending_hero:
            return
        if self._pending_hero in self.get_used_heroes():
            self._pending_label.setText(f"Duplicate hero not allowed: {self._pending_hero}")
            return

        if self._step >= len(TURN_SEQUENCE):
            self._pending_label.setText("Draft complete. Reset to start a new draft.")
            return

        expected_team, expected_action = TURN_SEQUENCE[self._step]
        if self._pending_team != expected_team or self._pending_action != expected_action:
            self._pending_label.setText(
                f"Step {self._step + 1} requires {expected_team} {expected_action}."
            )
            return

        self._step += 1
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(str(self._step)))
        self._table.setItem(row, 1, QTableWidgetItem(expected_team))
        self._table.setItem(row, 2, QTableWidgetItem(f"{expected_action.title()}: {self._pending_hero}"))

        team_bg = QColor(34, 56, 80, 70) if expected_team == TEAM_A else QColor(93, 64, 17, 70)
        action_fg = QColor(PICK_COLOR) if expected_action == "PICK" else QColor(BAN_COLOR)
        neutral_fg = QColor(230, 230, 230)

        for col in range(3):
            item = self._table.item(row, col)
            if item is None:
                continue
            item.setBackground(team_bg)
            item.setForeground(neutral_fg)

        action_item = self._table.item(row, 2)
        if action_item is not None:
            action_item.setForeground(action_fg)

        self._history.append(
            {
                "team": expected_team,
                "action": expected_action,
                "hero": self._pending_hero,
            }
        )

        self._pending_hero = ""
        self._pending_label.setText(f"Pending: none | Next: {self.get_next_step_text()}")
        self._refresh_status_text()
        self.draft_changed.emit()

    def _undo(self) -> None:
        n = self._table.rowCount()
        if n > 0:
            self._table.removeRow(n - 1)
            self._step = max(0, self._step - 1)
            if self._history:
                self._history.pop()
            self._pending_hero = ""
            self._pending_label.setText(f"Pending: none | Next: {self.get_next_step_text()}")
            self._refresh_status_text()
            self.draft_changed.emit()

    def _auto_pick(self) -> None:
        recs_path = _ANALYSIS_DIR / "draft_recommendations.csv"
        try:
            df = pd.read_csv(recs_path)
            if not df.empty and "hero" in df.columns:
                expected_team, expected_action = TURN_SEQUENCE[self._step] if self._step < len(TURN_SEQUENCE) else (TEAM_A, "PICK")
                used = self.get_used_heroes()
                for _, row in df.iterrows():
                    hero = str(row.get("hero", "")).strip()
                    if hero and hero not in used:
                        self.set_pending(hero, expected_team, expected_action)
                        break
        except (EmptyDataError, FileNotFoundError):
            pass
