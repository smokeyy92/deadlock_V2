from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .dataset_status_panel import DatasetStatusPanel
from .draft_timeline_panel import TEAM_A, TEAM_B, DraftTimelinePanel
from .hero_selector import HeroSelector
from .pipeline_panel import PipelinePanel
from .recommendation_panel import RecommendationPanel
from .team_analysis_panel import TeamAnalysisPanel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Deadlock Draft Analyzer")
        self.resize(1440, 900)
        self._build_ui()
        self._connect_signals()

    @staticmethod
    def _main_script_path() -> Path:
        return Path(__file__).resolve().parent.parent / "main.py"

    @staticmethod
    def _processed_heroes_path() -> Path:
        return Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "heroes.json"

    @staticmethod
    def _processed_matches_path() -> Path:
        return Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "matches.json"

    @staticmethod
    def _hero_vs_hero_path() -> Path:
        return Path(__file__).resolve().parent.parent.parent / "data" / "analysis" / "hero_vs_hero_matrix.csv"

    # ── layout ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Central area: hero selectors + draft timeline
        central = QWidget()
        self.setCentralWidget(central)
        center_layout = QVBoxLayout(central)
        center_layout.setContentsMargins(6, 6, 6, 6)
        center_layout.setSpacing(6)

        # Selector row
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel(f"<b>{TEAM_A}</b>"))
        self.sel_a = HeroSelector(f"{TEAM_A} hero")
        sel_row.addWidget(self.sel_a)
        self.btn_add_a = QPushButton(f"Add to {TEAM_A}  ▶")
        self.btn_add_a.setVisible(False)
        sel_row.addWidget(self.btn_add_a)
        sel_row.addStretch()
        self.btn_add_b = QPushButton(f"◀  Add to {TEAM_B}")
        self.btn_add_b.setVisible(False)
        sel_row.addWidget(self.btn_add_b)
        self.sel_b = HeroSelector(f"{TEAM_B} hero")
        sel_row.addWidget(self.sel_b)
        sel_row.addWidget(QLabel(f"<b>{TEAM_B}</b>"))
        center_layout.addLayout(sel_row)

        # Draft timeline
        self.timeline = DraftTimelinePanel()
        center_layout.addWidget(self.timeline)

        # Left dock: pipeline controls + dataset status
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(4)
        self.pipeline = PipelinePanel()
        self.ds_status = DatasetStatusPanel()
        left_layout.addWidget(self.pipeline)
        left_layout.addWidget(self.ds_status)

        left_dock = QDockWidget("Controls", self)
        left_dock.setWidget(left_widget)
        left_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)

        # Right dock: recommendations
        self.rec_panel = RecommendationPanel()
        right_dock = QDockWidget("Recommendations", self)
        right_dock.setWidget(self.rec_panel)
        right_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_dock)

        # Bottom dock: team analysis
        self.team_panel = TeamAnalysisPanel()
        bottom_dock = QDockWidget("Team Analysis", self)
        bottom_dock.setWidget(self.team_panel)
        bottom_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom_dock)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready — run the pipeline to populate datasets.")

    # ── signals ──────────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self.btn_add_a.clicked.connect(self._add_team_a)
        self.btn_add_b.clicked.connect(self._add_team_b)
        self.sel_a.hero_selected.connect(self._queue_team_a)
        self.sel_b.hero_selected.connect(self._queue_team_b)
        self.pipeline.relaunch_requested.connect(self._relaunch_app)
        self.timeline.draft_changed.connect(self._on_draft_changed)
        self.pipeline.pipeline_done.connect(self._on_pipeline_done)

    # ── slots ────────────────────────────────────────────────────────────────

    def _add_team_a(self) -> None:
        hero = self.sel_a.get_selected()
        if hero:
            ok = self.timeline.set_pending(hero, TEAM_A, "PICK")
            if not ok:
                self.statusBar().showMessage(self.timeline.get_next_step_text())

    def _add_team_b(self) -> None:
        hero = self.sel_b.get_selected()
        if hero:
            ok = self.timeline.set_pending(hero, TEAM_B, "PICK")
            if not ok:
                self.statusBar().showMessage(self.timeline.get_next_step_text())

    def _queue_team_a(self, hero: str) -> None:
        ok = self.timeline.set_pending(hero, TEAM_A, "PICK")
        if ok:
            self.statusBar().showMessage(f"Queued: {hero}. Click Confirm Action.")

    def _queue_team_b(self, hero: str) -> None:
        ok = self.timeline.set_pending(hero, TEAM_B, "PICK")
        if ok:
            self.statusBar().showMessage(f"Queued: {hero}. Click Confirm Action.")

    def _on_draft_changed(self) -> None:
        team_a = self.timeline.get_team_a_picks()
        team_b = self.timeline.get_team_b_picks()
        self.rec_panel.refresh(team_a, team_b)
        self.team_panel.update_teams(team_a, team_b)
        if self.timeline.is_draft_complete() and len(team_a) == 6 and len(team_b) == 6:
            win_pct, sample_size, source = self._compute_draft_win_prediction(team_a, team_b)
            self.team_panel.set_win_prediction(win_pct, sample_size, source)
        else:
            self.team_panel.set_win_prediction(None)
        self.statusBar().showMessage(
            f"{TEAM_A}: {len(team_a)} pick(s)  |  {TEAM_B}: {len(team_b)} pick(s)  |  Next: {self.timeline.get_next_step_text()}"
        )

    def _on_pipeline_done(self) -> None:
        self.ds_status.refresh()
        self.sel_a.reload()
        self.sel_b.reload()
        self.rec_panel.refresh()
        self.statusBar().showMessage(f"Pipeline step complete. Next: {self.timeline.get_next_step_text()}")

    def _relaunch_app(self) -> None:
        main_script = self._main_script_path()
        subprocess.Popen([sys.executable, str(main_script), "gui"], cwd=str(main_script.parent.parent))
        self.close()

    def _hero_name_to_id_map(self) -> dict[str, str]:
        heroes_path = self._processed_heroes_path()
        if not heroes_path.exists():
            return {}
        try:
            rows = json.loads(heroes_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

        mapping: dict[str, str] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            hero_id = str(row.get("hero_id") or row.get("id") or "").strip()
            if name and hero_id:
                mapping[name] = hero_id
        return mapping

    def _compute_draft_win_prediction(self, team_a: list[str], team_b: list[str]) -> tuple[float | None, int, str]:
        hero_id_map = self._hero_name_to_id_map()
        team_a_ids = sorted([hero_id_map.get(name, name) for name in team_a])
        team_b_ids = sorted([hero_id_map.get(name, name) for name in team_b])

        matches_path = self._processed_matches_path()
        if matches_path.exists():
            try:
                matches = json.loads(matches_path.read_text(encoding="utf-8"))
            except Exception:
                matches = []

            exact_games = 0
            exact_wins = 0
            for match in matches:
                if not isinstance(match, dict):
                    continue
                left = sorted([str(v) for v in match.get("team_a_heroes", [])])
                right = sorted([str(v) for v in match.get("team_b_heroes", [])])
                winner = str(match.get("winner") or "").lower()

                if left == team_a_ids and right == team_b_ids:
                    exact_games += 1
                    if winner == "team_a":
                        exact_wins += 1
                elif left == team_b_ids and right == team_a_ids:
                    exact_games += 1
                    if winner == "team_b":
                        exact_wins += 1

            if exact_games > 0:
                return (100.0 * exact_wins / exact_games, exact_games, "exact composition")

        hvh_path = self._hero_vs_hero_path()
        if not hvh_path.exists():
            return (None, 0, "")

        weighted_wins = 0.0
        weighted_games = 0
        try:
            with hvh_path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                hvh_map: dict[tuple[str, str], tuple[float, int]] = {}
                for row in reader:
                    hero_a = str(row.get("hero_a") or "")
                    hero_b = str(row.get("hero_b") or "")
                    if not hero_a or not hero_b:
                        continue
                    try:
                        winrate = float(row.get("winrate") or 0.5)
                        games = int(float(row.get("games") or 0))
                    except ValueError:
                        continue
                    hvh_map[(hero_a, hero_b)] = (winrate, games)

            for hero_a in team_a_ids:
                for hero_b in team_b_ids:
                    winrate, games = hvh_map.get((hero_a, hero_b), (0.5, 0))
                    if games <= 0:
                        continue
                    weighted_wins += winrate * games
                    weighted_games += games
        except Exception:
            return (None, 0, "")

        if weighted_games <= 0:
            return (None, 0, "")

        return (100.0 * weighted_wins / weighted_games, weighted_games, "hero matchups")
