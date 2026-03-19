import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from PySide6.QtCore import QObject, Signal

# Dictionary to map file names to GUI hero names
HERO_NAME_MAP = {
    "bull_card.webp": "Abrams",
    "fencer_card.webp": "Apollo",
    "bebop_card.webp": "Bebop",
    "punkgoat_card.webp": "Billy",
    "nano_card.webp": "Calico",
    "unicorn_card.webp": "Celeste",
    "drifter_card.webp": "Drifter",
    "sumo_card.webp": "Dynamo",
    "necro_card.webp": "Graves",
    "archer_card.webp": "Grey Talon",
    "haze_card.webp": "Haze",
    "astro_card.webp": "Holliday",
    "inferno_card.webp": "Infernus",
    "tengu_card.webp": "Ivy",
    "kelvin_card.webp": "Kelvin",
    "spectre_card.webp": "Lady Geist",
    "lash_card.webp": "Lash",
    "engineer_card.webp": "McGinnis",
    "vampirebat_card.webp": "Mina",
    "mirage_card.webp": "Mirage",
    "digger_card.webp": "Mo & Krill",
    "bookworm_card.webp": "Paige",
    "chrono_card.webp": "Paradox",
    "synth_card.webp": "Pocket",
    "familiar_card.webp": "Rem",
    "gigawatt_card.webp": "Seven",
    "shiv_card.webp": "Shiv",
    "werewolf_card.webp": "Silver",
    "magician_card.webp": "Sinclair",
    "doorman_card.webp": "The Doorman",
    "priest_card.webp": "Venator",
    "frank_card.webp": "Victor",
    "hornet_card.webp": "Vindicta",
    "viscous_card.webp": "Viscous",
    "kali_card.webp": "Vyper",
    "warden_card.webp": "Warden",
    "wraith_card.webp": "Wraith",
    "yamato_card.webp": "Yamato"
}

# 1. Create a dedicated signal class
class BridgeSignals(QObject):
    # This signal will carry the entire data dictionary
    update_received = Signal(dict)

# Global instance of signals
bridge_signals = BridgeSignals()

app = Flask(__name__)
CORS(app)

@app.route('/update_draft', methods=['POST'])
def update_draft():
    data = request.json
    if data:
        # 2. Just emit the signal with all data
        # Qt will automatically handle thread safety
        bridge_signals.update_received.emit(data)
        return jsonify({"status": "received"}), 200
    return jsonify({"status": "error"}), 400

def start_bridge(gui_instance):
    # 3. Connect the signal to the GUI method
    # This ensures process_external_update runs in the GUI thread
    bridge_signals.update_received.connect(gui_instance.process_external_update_from_dict)
    
    threading.Thread(target=lambda: app.run(port=5000, debug=False, use_reloader=False), daemon=True).start()
