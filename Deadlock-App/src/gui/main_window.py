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
    QFrame,
    QStackedWidget
)
from PySide6.QtCore import Slot

from .dataset_status_panel import DatasetStatusPanel
from .draft_timeline_panel import TEAM_A, TEAM_B, VisualDraftPanel, DraftTimelinePanel
from .hero_selector import HeroSelector
from .pipeline_panel import PipelinePanel
from .recommendation_panel import RecommendationPanel
from .team_analysis_panel import TeamAnalysisPanel
from .lane_optimizer_panel import LaneOptimizerPanel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Deadlock Draft Analyzer")
        self.resize(1440, 1080)
        self._build_ui()
        self._connect_signals()
        self._toggle_view_mode(True)

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
        """Constructs the modern gaming UI with toggleable view modes using QStackedWidget."""
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
    
        # Main vertical layout for the central area
        center_layout = QVBoxLayout(central)
        center_layout.setContentsMargins(15, 15, 15, 15)
        center_layout.setSpacing(10)

        # --- HEADER ROW (Selectors & Controls) ---
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #252525; border-radius: 8px; border: 1px solid #3d3d3d;")
        header_layout = QHBoxLayout(header_frame)
        header_frame.setFixedHeight(65)
        header_layout.setContentsMargins(10, 5, 10, 5)

        buttons_column = QVBoxLayout()
        buttons_column.setSpacing(4)
        buttons_column.setContentsMargins(0, 0, 0, 0)

        self.btn_toggle_view = QPushButton("VIEW: VISUAL")
        self.btn_toggle_view.setFixedWidth(130)
        self.btn_toggle_view.setCheckable(True)
        self.btn_toggle_view.setChecked(True)
        self.btn_toggle_view.setStyleSheet("""
            QPushButton { background-color: #333; color: #aaa; border: 1px solid #555; }
            QPushButton:checked { background-color: #4a9eff; color: white; border: 1px solid #4a9eff; }
        """)
        buttons_column.addWidget(self.btn_toggle_view)

        header_layout.addSpacing(10)
        self.btn_toggle_controls = QPushButton("SHOW CONTROLS")
        self.btn_toggle_controls.setFixedWidth(130)
        self.btn_toggle_controls.setCheckable(True)
        self.btn_toggle_controls.setChecked(False)
        self.btn_toggle_controls.setStyleSheet("""
            QPushButton { background-color: #333; color: #aaa; border: 1px solid #555; }
            QPushButton:checked { background-color: #444; color: #63BE7B; border: 1px solid #63BE7B; }
        """)
        buttons_column.addWidget(self.btn_toggle_controls)
        
        header_layout.addLayout(buttons_column)
        header_layout.addStretch(1)

        self.sel_a = HeroSelector(f"Search {TEAM_A} hero...")
        header_layout.addWidget(self.sel_a, 2)
        self.btn_add_a = QPushButton("ADD PICK")
        self.btn_add_a.setObjectName("AddBtnA")
        self.btn_add_a.setVisible(False)
        header_layout.addWidget(self.btn_add_a)

        header_layout.addSpacing(20)

        self.btn_add_b = QPushButton("ADD PICK")
        self.btn_add_b.setObjectName("AddBtnB")
        self.btn_add_b.setVisible(False)
        header_layout.addWidget(self.btn_add_b)
        self.sel_b = HeroSelector(f"Search {TEAM_B} hero...")
        header_layout.addWidget(self.sel_b, 2)

        center_layout.addWidget(header_frame)

        # --- CONTENT AREA: QStackedWidget (Stabilizes layout during mode switch) ---
        self.mode_stack = QStackedWidget()
    
        # --- Mode 1: Visual View (Hero Cards) ---
        self.visual_container = QWidget()
        v_layout = QVBoxLayout(self.visual_container)
        v_layout.setContentsMargins(0, 0, 0, 0)
    
        self.panel_a = VisualDraftPanel(TEAM_A, "#ff9e4a") # Hidden King - Orange
        self.panel_b = VisualDraftPanel(TEAM_B, "#4a9eff") # Archmother - Blue
        v_layout.addWidget(self.panel_a)
        v_layout.addWidget(self.panel_b)
        v_layout.addStretch(1) # Internal stretch keeps cards pinned correctly
    
        # --- Mode 2: Classic View (Original Table) ---
        self.timeline = DraftTimelinePanel()
        # No need to setVisible(False) manually, QStackedWidget handles it
    
        # Add modes to stack
        self.mode_stack.addWidget(self.visual_container) # Index 0
        self.mode_stack.addWidget(self.timeline)         # Index 1
    
        center_layout.addWidget(self.mode_stack)

        # Final stretch at the bottom to keep everything compact at the top
        center_layout.addStretch(1)

        # --- RESTORED DOCK SETUP ---
        self._setup_docks()

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready — waiting for draft actions...")

    def _setup_docks(self) -> None:
        """Initializes side and bottom docks, hiding CONTROLS by default."""
        # --- LEFT DOCK: Controls ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.pipeline = PipelinePanel()
        self.ds_status = DatasetStatusPanel()
        left_layout.addWidget(self.pipeline)
        left_layout.addWidget(self.ds_status)
        left_layout.addStretch()

        # Save reference to the dock to toggle it later
        self.controls_dock = self._create_dock("CONTROLS", left_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.controls_dock)
        
        # --- HIDE BY DEFAULT ---
        self.controls_dock.setVisible(False)

        # Left dock: Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.pipeline = PipelinePanel()
        self.ds_status = DatasetStatusPanel()
        left_layout.addWidget(self.pipeline)
        left_layout.addWidget(self.ds_status)
        left_layout.addStretch()

        self.controls_dock = self._create_dock("CONTROLS", left_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.controls_dock)
        self.controls_dock.hide() 

        # Right dock: Analysis
        self.right_container = QWidget()
        self.right_container.setFixedWidth(700) 
        self.right_layout = QVBoxLayout(self.right_container)

        self.right_layout.setContentsMargins(0, 0, 0, 0) 
        self.right_layout.setSpacing(0) 
        
        self.rec_panel = RecommendationPanel()
        self.lane_panel = LaneOptimizerPanel()
        self.lane_panel.setVisible(False)
        
        self.right_layout.addWidget(self.rec_panel)
        self.right_layout.addWidget(self.lane_panel)

        right_dock = self._create_dock("DRAFT ANALYSIS", self.right_container)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_dock)

        # Bottom dock: Team Analysis
        self.team_panel = TeamAnalysisPanel()
        bottom_dock = self._create_dock("TEAM COMPOSITION", self.team_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom_dock)

    def _create_dock(self, title: str, widget: QWidget) -> QDockWidget:
        """Helper to create a standard QDockWidget with uniform features."""
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        return dock

    def _connect_signals(self) -> None:
        """Binds UI interactions to internal logic slots."""
        self.btn_add_a.clicked.connect(self._add_team_a)
        self.btn_add_b.clicked.connect(self._add_team_b)
        self.sel_a.hero_selected.connect(self._queue_team_a)
        self.sel_b.hero_selected.connect(self._queue_team_b)
        self.pipeline.relaunch_requested.connect(self._relaunch_app)
        self.timeline.draft_changed.connect(self._on_draft_changed)
        self.pipeline.pipeline_done.connect(self._on_pipeline_done)
        self.lane_panel.team_changed.connect(self._on_draft_changed)
        self.btn_toggle_view.toggled.connect(self._toggle_view_mode)
        self.btn_toggle_controls.toggled.connect(self._toggle_controls_panel)
        self.controls_dock.visibilityChanged.connect(self._on_controls_visibility_changed)

    @Slot(bool)
    def _toggle_controls_panel(self, visible: bool) -> None:
        """Toggles the visibility of the left Controls dock."""
        self.controls_dock.setVisible(visible)
        self.btn_toggle_controls.setText("HIDE CONTROLS" if visible else "SHOW CONTROLS")

    def _on_controls_visibility_changed(self, visible: bool) -> None:
        """Syncs the header button state if the dock is closed manually."""
        self.btn_toggle_controls.setChecked(visible)
        self.btn_toggle_controls.setText("HIDE CONTROLS" if visible else "SHOW CONTROLS")

    @Slot(bool)
    def _toggle_view_mode(self, is_visual: bool) -> None:
        """Switch index in the stack instead of manual hiding."""
        self.mode_stack.setCurrentIndex(0 if is_visual else 1)
        
        self.sel_a.setVisible(not is_visual)
        self.sel_b.setVisible(not is_visual)
        if is_visual:
            self.btn_add_a.setVisible(False)
            self.btn_add_b.setVisible(False)
        
        self.btn_toggle_view.setText("VIEW: VISUAL" if is_visual else "VIEW: CLASSIC")

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
        history = []
        if hasattr(self.timeline, 'get_history'):
            history = self.timeline.get_history()
        elif hasattr(self.timeline, '_history'):
            history = self.timeline._history

        picks_a, bans_a = [], []
        picks_b, bans_b = [], []

        for i, entry in enumerate(history, 1):
            hero_name = entry.get('hero', 'Unknown')
            step_num = entry.get('step', i) 
            
            item = {"name": hero_name, "step": step_num}
            
            team = entry.get('team')
            action = entry.get('action', 'PICK')

            if team == TEAM_A:
                if action == "PICK": picks_a.append(item)
                else: bans_a.append(item)
            else:
                if action == "PICK": picks_b.append(item)
                else: bans_b.append(item)

        icon_func = self.lane_panel._get_hero_icon_path 
        self.panel_a.update_draft(picks_a, bans_a, icon_func)
        self.panel_b.update_draft(picks_b, bans_b, icon_func)

        team_a = self.timeline.get_team_a_picks()
        team_b = self.timeline.get_team_b_picks()

        is_complete = self.timeline.is_draft_complete() and len(team_a) == 6 and len(team_b) == 6

        if is_complete:
            self.rec_panel.setVisible(False)
            self.lane_panel.setVisible(True)
            self.lane_panel.update_data(team_a, team_b)
        else:
            self.rec_panel.setVisible(True)
            self.lane_panel.setVisible(False)
            self.rec_panel.refresh(team_a, team_b)

        self.team_panel.update_teams(team_a, team_b)
        
        if is_complete:
            win_pct, sample_size, source = self._compute_draft_win_prediction(team_a, team_b)
            self.team_panel.set_win_prediction(win_pct, sample_size, source)
        else:
            self.team_panel.set_win_prediction(None)

        self.statusBar().showMessage(
            f"{TEAM_A}: {len(team_a)} | {TEAM_B}: {len(team_b)} | Next: {self.timeline.get_next_step_text()}"
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

            # --- Integration with Bridge Server ---
            
    from PySide6.QtCore import Slot # Make sure this is in imports

    @Slot(dict)
    def process_external_update_from_dict(self, data):
        """ Intermediate slot to handle data from Signal """
        if data.get('event') == 'DRAFT_UPDATE':
            current = data.get('current')
            full_draft = data.get('fullDraft')
            count = data.get('count')
            
            # Call your main processing logic
            self.process_external_update(current, full_draft, count)

    @Slot(object, object, int)
    def process_external_update(self, current, full_draft, script_count):
        """ 
        Processes a single update but also verifies the total count.
        If counts mismatch, synchronizes the entire draft.
        """
        # Get current count in GUI (picks + bans)
        gui_count = len(self.timeline.get_used_heroes())
        
        # Scenario A: Perfect sequence (1 new hero added)
        if script_count == gui_count + 1:
            self._apply_single_pick(current)
            self.statusBar().showMessage(f"Added: {current['heroFile']}")

        # Scenario B: Desync or late start (Script has more heroes than GUI)
        elif script_count > gui_count:
            print(f"[SYNC] Desync detected. GUI: {gui_count}, Script: {script_count}. Repairing...")
            self._synchronize_all(full_draft)
            self.statusBar().showMessage(f"Draft Synchronized ({script_count} heroes)")

        # Scenario C: Already in sync or script reset
        elif script_count < gui_count:
             print("[SYNC] Script has fewer heroes. Resetting GUI to match.")
             self._synchronize_all(full_draft)

        self._on_draft_changed()

    def _apply_single_pick(self, entry):
        """ Forcefully adds a hero to the timeline, ignoring internal TURN_SEQUENCE checks """
        from bridge_server import HERO_NAME_MAP
        from PySide6.QtWidgets import QTableWidgetItem
        from PySide6.QtGui import QColor

        file_name = entry.get('heroFile')
        hero_name = HERO_NAME_MAP.get(file_name, file_name.replace('_card.webp', '').capitalize())
        team_label = "Hidden King" if entry.get('team') == 'AMBER' else "Archmother"
        action_type = entry.get('type') # PICK or BAN

        # 1. Manually update internal state
        self.timeline._step += 1
        self.timeline._history.append({
            "hero": hero_name,
            "team": team_label,
            "action": action_type
        })

        # 2. Directly update the UI Table
        row = self.timeline._table.rowCount()
        self.timeline._table.insertRow(row)
        
        self.timeline._table.setItem(row, 0, QTableWidgetItem(str(self.timeline._step)))
        self.timeline._table.setItem(row, 1, QTableWidgetItem(team_label))
        self.timeline._table.setItem(row, 2, QTableWidgetItem(f"{action_type.title()}: {hero_name}"))

        # 3. Apply Styling
        team_bg = QColor(93, 64, 17, 70) if team_label == "Hidden King" else QColor(34, 56, 80, 70)
        action_fg = QColor("#2ECC71") if action_type == "PICK" else QColor("#E74C3C")
        
        for col in range(3):
            item = self.timeline._table.item(row, col)
            if item:
                item.setBackground(team_bg)
                if col == 2:
                    item.setForeground(action_fg)

        # 4. Update the status labels in timeline
        self.timeline._refresh_status_text()


    def _synchronize_all(self, full_draft):
        """ Rebuilds the draft from scratch based on the full list from script """
        self.timeline.reset()
        for entry in full_draft:
            self._apply_single_pick(entry)
