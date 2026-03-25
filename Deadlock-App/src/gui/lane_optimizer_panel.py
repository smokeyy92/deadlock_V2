from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QComboBox, QScrollArea
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QPixmap, QDrag, QAction
from lane_setup import SynergyEngine
import os

class HeroSlot(QFrame):
    """Individual slot for a single hero. 6 of these in total."""
    hero_dropped = Signal(str, int, int) # hero_name, lane_id, slot_index

    def __init__(self, lane_id, slot_index):
        super().__init__()
        self.lane_id = lane_id
        self.slot_index = slot_index
        self.setAcceptDrops(True)
        self.setFixedSize(90, 90)
        
        # Style matches the empty state or placeholder
        self.setStyleSheet("""
            QFrame { 
                background: rgba(0, 0, 0, 20); 
                border: 1px dashed #333; 
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignCenter)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
            self.setStyleSheet("background: #333; border: 1px solid #63BE7B; border-radius: 8px;")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("background: rgba(0, 0, 0, 20); border: 1px dashed #333; border-radius: 8px;")

    def dropEvent(self, event):
        hero_name = event.mimeData().text()
        self.hero_dropped.emit(hero_name, self.lane_id, self.slot_index)
        self.dragLeaveEvent(None)

class DraggableHero(QLabel):
    def __init__(self, name, icon_pix, parent=None):
        super().__init__(parent)
        self.hero_name = name
        self.setPixmap(icon_pix)
        self.setFixedSize(90, 90)
        self.setScaledContents(False)
        self.setCursor(Qt.OpenHandCursor)
        self.setAlignment(Qt.AlignCenter) 
        self.setStyleSheet("background: transparent; border: none;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.hero_name)
            drag.setMimeData(mime)
            drag.setPixmap(self.pixmap())
            drag.setHotSpot(event.position().toPoint())
            drag.exec_(Qt.MoveAction)

class InteractiveLane(QWidget):
    """Container for two HeroSlots."""
    def __init__(self, lane_id, lane_name, drop_callback):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

        # 1. Title
        title = QLabel(lane_name)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #777; font-size: 10px; font-weight: bold;")
        self.layout.addWidget(title)
        
        # 2. Hero Slots Group (6 slots total: 2 per lane)
        self.slots_layout = QHBoxLayout()
        self.slots_layout.setContentsMargins(0, 0, 0, 0)
        self.slots_layout.setSpacing(-15) # Maintain the SYNERGY FOCUS overlap style
        self.slots_layout.setAlignment(Qt.AlignCenter)
        
        self.slots = []
        for i in range(2):
            slot = HeroSlot(lane_id, i)
            slot.hero_dropped.connect(drop_callback)
            self.slots.append(slot)
            self.slots_layout.addWidget(slot)
            
        self.layout.addLayout(self.slots_layout)

        # 3. Winrate
        self.wr_label = QLabel("0.0%")
        self.wr_label.setAlignment(Qt.AlignCenter)
        self.wr_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        self.layout.addWidget(self.wr_label)

class LaneOptimizerPanel(QWidget):
    # Signal to request data refresh when team selection changes
    team_changed = Signal()

    def __init__(self):
        super().__init__()
        self.engine = SynergyEngine()
        self._current_heroes = {"Team A": [], "Team B": []}
        self.manual_setup = {} 
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
        """Triggered when the target team is switched in the UI."""
        # Clear the manual setup so it re-initializes with the new team's heroes
        self.manual_setup = {} 
        # Refresh the display to show the new team's data immediately
        self.refresh_display()
        # Notify other components if necessary
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

    def _get_hero_icon_path(self, hero_name):
        """Returns the absolute path to the hero icon webp file."""
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
            return ""
        return os.path.join("data", "hero_webp", img_name)

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
        STRATEGY_NAMES = ["SYNERGY FOCUS", "LANE EFFICIENCY", "BALANCED SETUP"]
        top_setups = self.engine.get_top_lane_setups(heroes, top_n=3)

        for idx, setup in enumerate(top_setups):
            # --- 1. Calculate color and strategy names FIRST ---
            avg_wr = setup['average_winrate']
            val_color = "#63BE7B" if avg_wr > 0.52 else "#F8696B" if avg_wr < 0.48 else "#FFFFFF"
            STRATEGY_NAMES = ["SYNERGY FOCUS", "LANE EFFICIENCY", "BALANCED SETUP"]
            strategy_name = STRATEGY_NAMES[idx] if idx < len(STRATEGY_NAMES) else "OPTIMIZED SETUP"

            # --- 2. CREATE THE BLOCK (defines setup_block and block_layout) ---
            setup_block = QFrame()
            setup_block.setStyleSheet("""
                QFrame {
                    background-color: #2a2a2a;
                    border: 1px solid #3d3d3d;
                    border-radius: 12px;
                }
                QLabel { border: none; background: transparent; }
            """)
            
            block_layout = QVBoxLayout(setup_block)
            block_layout.setContentsMargins(12, 6, 12, 8)
            block_layout.setSpacing(2)

            # --- 3. Add Header to the block ---
            header_text = (
                f"<span style='color: #aaaaaa; font-weight: bold;'>{strategy_name} WR: </span>"
                f"<span style='color: {val_color}; font-weight: bold;'>{avg_wr:.1%}</span>"
            )
            
            avg_label = QLabel(header_text)
            avg_label.setAlignment(Qt.AlignCenter)
            avg_label.setStyleSheet("font-size: 13px; margin-bottom: 5px;")
            block_layout.addWidget(avg_label) # <--- block_layout is used here

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
                unit_layout.setSpacing(2) 

                # Lane Name (Visible but compact)
                l_title = QLabel(LANE_NAMES.get(lane['lane_id']))
                l_title.setAlignment(Qt.AlignCenter)
                l_title.setStyleSheet("color: #777; font-size: 10px; font-weight: bold;")
                unit_layout.addWidget(l_title)

                # Hero Group - NO BORDER, increased size
                hero_group = QWidget()
                hero_group.setFixedHeight(92) # Enough room for large icons
                
                group_layout = QHBoxLayout(hero_group)
                group_layout.setContentsMargins(0, 0, 0, 0)
                group_layout.setSpacing(6)
                group_layout.setAlignment(Qt.AlignCenter)

                for hero in lane['pair']:
                    icon_pix = self._get_hero_icon(hero)
                    if icon_pix:
                        # Increased icon size (85x85) for better visibility
                        icon_pix = icon_pix.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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

        self._add_manual_setup_block(heroes, LANE_NAMES)
        
        # Anchor everything at the top
        self.lanes_layout.addStretch()

    def _add_manual_setup_block(self, heroes, lane_names):
        if not heroes or len(heroes) < 6: return

        # Initialize manual setup as a fixed structure: {lane_id: [HeroSlot0, HeroSlot1]}
        if not self.manual_setup:
            initial_list = self.engine.get_top_lane_setups(heroes, top_n=1)
            if initial_list:
                best = initial_list[0]
                for l in best['lanes']:
                    # Store as exact list of 2 elements
                    self.manual_setup[l['lane_id']] = list(l['pair'])

        setup_data = self.engine.calculate_setup_details(self.manual_setup)
        avg_wr = setup_data['average_winrate']
        val_color = "#63BE7B" if avg_wr > 0.52 else "#F8696B" if avg_wr < 0.48 else "#FFFFFF"

        manual_block = QFrame()
        manual_block.setStyleSheet("background-color: #2a2a2a; border: 1px solid #3d3d3d; border-radius: 12px;")
        block_layout = QVBoxLayout(manual_block)
        block_layout.setContentsMargins(12, 6, 12, 8)

        header_text = (f"<span style='color: #aaaaaa; font-weight: bold;'>MANUAL OPTIMIZER WR: </span>"
                       f"<span style='color: {val_color}; font-weight: bold;'>{avg_wr:.1%}</span>")
        avg_label = QLabel(header_text)
        avg_label.setAlignment(Qt.AlignCenter)
        block_layout.addWidget(avg_label)

        lanes_row = QHBoxLayout()
        for l_id in sorted(lane_names.keys()):
            lane_widget = InteractiveLane(l_id, lane_names[l_id], self._on_hero_dropped)
            
            lane_info = next((l for l in setup_data['lanes'] if l['lane_id'] == l_id), None)
            l_wr = lane_info['wr'] if lane_info else 0.5
            wr_color = "#63BE7B" if l_wr > 0.52 else "#F8696B" if l_wr < 0.48 else "#FFFFFF"
            lane_widget.wr_label.setText(f"{l_wr:.1%}")
            lane_widget.wr_label.setStyleSheet(f"color: {wr_color}; font-weight: bold;")

            # Fill the 2 slots of this lane
            for i in range(2):
                h_name = self.manual_setup[l_id][i]
                pix = self._get_hero_icon(h_name)
                if pix:
                    hero_label = DraggableHero(h_name, pix.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    lane_widget.slots[i].layout.addWidget(hero_label)
                    # When slot is full, remove the dashed border style
                    lane_widget.slots[i].setStyleSheet("background: transparent; border: none;")
            
            lanes_row.addWidget(lane_widget)
        
        block_layout.addLayout(lanes_row)
        self.lanes_layout.addWidget(manual_block)

    def _on_hero_dropped(self, hero_name, to_lane, to_slot):
        """Precise swap logic for 6 individual slots."""
        # 1. Find where the dragged hero was originally
        from_lane, from_slot = None, None
        for l_id, pair in self.manual_setup.items():
            if hero_name in pair:
                from_lane = l_id
                from_slot = pair.index(hero_name)
                break
        
        if from_lane is None: return
        if from_lane == to_lane and from_slot == to_slot: return

        # 2. Get the hero currently occupying the target slot
        target_hero = self.manual_setup[to_lane][to_slot]

        # 3. SWAP them
        self.manual_setup[to_lane][to_slot] = hero_name
        self.manual_setup[from_lane][from_slot] = target_hero

        self.refresh_display()
