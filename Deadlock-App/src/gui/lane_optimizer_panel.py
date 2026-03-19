from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QComboBox, QScrollArea
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from lane_setup import SynergyEngine
import os

class LaneOptimizerPanel(QWidget):
    # Signal to request data refresh when team selection changes
    team_changed = Signal()

    def __init__(self):
        super().__init__()
        self.engine = SynergyEngine()
        self._current_heroes = {"Team A": [], "Team B": []}
        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Header with Team Selector
        header_layout = QHBoxLayout()
        self.title = QLabel("<b>LANE OPTIMIZER</b>")
        
        self.team_selector = QComboBox()
        self.team_selector.addItems(["Team A", "Team B"])
        self.team_selector.currentIndexChanged.connect(self._on_team_toggle)
        
        header_layout.addWidget(self.title)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("Target:"))
        header_layout.addWidget(self.team_selector)
        self.main_layout.addLayout(header_layout)

        # Scroll Area for Top 3 Results
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        
        self.container = QWidget()
        self.lanes_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)

        self.info_label = QLabel("Complete the draft to see Top 3 setups")
        self.info_label.setStyleSheet("color: #888888; font-style: italic;")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.lanes_layout.addWidget(self.info_label)

    def _on_team_toggle(self):
        self.team_changed.emit()

    def update_data(self, team_a: list[str], team_b: list[str]):
        self._current_heroes = {"Team A": team_a, "Team B": team_b}
        self.refresh_display()

    def _get_hero_icon(self, hero_name):
        """Helper to find image filename by hero name."""
        # Reverse mapping: Hero Name -> Filename
        HERO_IMAGE_BY_NAME = {
            "Abrams": "bull_card.webp", "Apollo": "fencer_card.webp", "Bebop": "bebop_card.webp",
            "Billy": "punkgoat_card.webp", "Calico": "nano_card.webp", "Celeste": "unicorn_card.webp",
            "Drifter": "drifter_card.webp", "Dynamo": "sumo_card.webp", "Graves": "necro_card.webp",
            "Grey Talon": "archer_card.webp", "Haze": "haze_card.webp", "Holliday": "astro_card.webp",
            "Infernus": "inferno_card.webp", "Ivy": "tengu_card.webp", "Kelvin": "kelvin_card.webp",
            "Lady Geist": "spectre_card.webp", "Lash": "lash_card.webp", "McGinnis": "engineer_card.webp",
            "Mina": "vampirebat_card.webp", "Mirage": "mirage_card.webp", "Mo & Krill": "digger_card.webp",
            "Paige": "bookworm_card.webp", "Paradox": "chrono_card.webp", "Pocket": "synth_card.webp",
            "Rem": "familiar_card.webp", "Seven": "gigawatt_card.webp", "Shiv": "shiv_card.webp",
            "Silver": "werewolf_card.webp", "Sinclair": "magician_card.webp", "The Doorman": "doorman_card.webp",
            "Venator": "priest_card.webp", "Victor": "frank_card.webp", "Vindicta": "hornet_card.webp",
            "Viscous": "viscous_card.webp", "Vyper": "kali_card.webp", "Warden": "warden_card.webp",
            "Wraith": "wraith_card.webp", "Yamato": "yamato_card.webp"
        }
        
        img_name = HERO_IMAGE_BY_NAME.get(hero_name)
        if not img_name:
            return None
            
        # Path to your images folder (adjust if necessary)
        path = os.path.join("data", "hero_webp", img_name) 
        if os.path.exists(path):
            pix = QPixmap(path)
            # Scale icon to a reasonable size (e.g., 24x24 or 32x32)
            return pix.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return None

    def refresh_display(self):
        # Clear the container from previous results
        while self.lanes_layout.count():
            item = self.lanes_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        # Global spacing for the whole panel
        self.lanes_layout.setSpacing(6) 
        self.lanes_layout.setContentsMargins(5, 5, 5, 5)

        selected_team = self.team_selector.currentText()
        heroes = self._current_heroes.get(selected_team, [])

        if len(heroes) != 6:
            msg = QLabel(f"Waiting for {selected_team}...")
            msg.setAlignment(Qt.AlignCenter)
            self.lanes_layout.addWidget(msg)
            return

        LANE_NAMES = {1: "LEFT LANE", 3: "MID LANE", 4: "RIGHT LANE"}
        top_setups = self.engine.get_top_lane_setups(heroes, top_n=3)

        for idx, setup in enumerate(top_setups, 1):
            # --- MAIN SETUP BLOCK ---
            setup_block = QFrame()
            setup_block.setStyleSheet("""
                QFrame {
                    background-color: #2a2a2a;
                    border: 1px solid #3d3d3d;
                    border-radius: 8px;
                }
                QLabel { border: none; background: transparent; }
            """)
            
            block_layout = QVBoxLayout(setup_block)
            block_layout.setContentsMargins(10, 6, 10, 8) 
            block_layout.setSpacing(2) # Minimal gap between header and lanes

            # 1. Header (TOP X WR) - Bold and Visible
            avg_wr = setup['average_winrate']
            val_color = "#63BE7B" if avg_wr > 0.52 else "#F8696B" if avg_wr < 0.48 else "#FFFFFF"
            
            avg_label = QLabel(
                f"<span style='color: #888; font-weight: bold;'>TOP {idx} WR: </span>"
                f"<span style='color: {val_color}; font-weight: bold;'>{avg_wr:.1%}</span>"
            )
            avg_label.setAlignment(Qt.AlignCenter)
            avg_label.setStyleSheet("font-size: 13px; margin-bottom: 2px;") 
            block_layout.addWidget(avg_label)

            # 2. Horizontal Row for the 3 lanes
            lanes_row_widget = QWidget()
            lanes_row_layout = QHBoxLayout(lanes_row_widget)
            lanes_row_layout.setContentsMargins(0, 0, 0, 0)
            lanes_row_layout.setSpacing(10)

            sorted_lanes = sorted(setup['lanes'], key=lambda x: x['lane_id'])

            for lane in sorted_lanes:
                lane_unit = QWidget()
                unit_layout = QVBoxLayout(lane_unit)
                unit_layout.setContentsMargins(0, 0, 0, 0)
                unit_layout.setSpacing(4) 

                # Lane Name (Visible but compact)
                l_title = QLabel(LANE_NAMES.get(lane['lane_id']))
                l_title.setAlignment(Qt.AlignCenter)
                l_title.setStyleSheet("color: #777; font-size: 10px; font-weight: bold;")
                unit_layout.addWidget(l_title)

                # Hero Group - NO BORDER, increased size
                hero_group = QWidget()
                hero_group.setFixedHeight(95) # Enough room for large icons
                
                group_layout = QHBoxLayout(hero_group)
                group_layout.setContentsMargins(0, 0, 0, 0)
                group_layout.setSpacing(10)
                group_layout.setAlignment(Qt.AlignCenter)

                for hero in lane['pair']:
                    icon_pix = self._get_hero_icon(hero)
                    if icon_pix:
                        # Increased icon size (85x85) for better visibility
                        icon_pix = icon_pix.scaled(85, 85, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        img_label = QLabel()
                        img_label.setPixmap(icon_pix)
                        img_label.setStyleSheet("background: transparent; border: none;")
                        group_layout.addWidget(img_label)

                unit_layout.addWidget(hero_group)

                # Lane Winrate (Large and Colored)
                wr = lane['wr']
                wr_color = "#63BE7B" if wr > 0.52 else "#F8696B" if wr < 0.48 else "#FFFFFF"
                wr_label = QLabel(f"{wr:.1%}")
                wr_label.setAlignment(Qt.AlignCenter)
                wr_label.setStyleSheet(f"color: {wr_color}; font-size: 15px; font-weight: bold;")
                unit_layout.addWidget(wr_label)

                lanes_row_layout.addWidget(lane_unit)

            block_layout.addWidget(lanes_row_widget)
            self.lanes_layout.addWidget(setup_block)

        # Anchor everything at the top
        self.lanes_layout.addStretch()
