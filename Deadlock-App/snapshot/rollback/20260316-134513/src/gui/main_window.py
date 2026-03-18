from __future__ import annotations

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
        self.btn_relaunch = QPushButton("Relaunch App")
        sel_row.addWidget(self.btn_relaunch)
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
        self.btn_relaunch.clicked.connect(self._relaunch_app)
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
