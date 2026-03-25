import json
import pandas as pd
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR) 
DATA_LANE_DIR = os.path.join(ROOT_DIR, "data", "lane")

os.makedirs(DATA_LANE_DIR, exist_ok=True)

INPUT_FILE = os.path.join(DATA_LANE_DIR, "lane_stats.json")

SYNERGY_JSON = os.path.join(DATA_LANE_DIR, "synergy_data.json")
LANE_STATS_JSON = os.path.join(DATA_LANE_DIR, "lane_data.json")
MATRIX_EXCEL = os.path.join(DATA_LANE_DIR, "synergy_statsheet.xlsx")

HERO_NAMES = {
    1: "Infernus", 2: "Seven", 3: "Vindicta", 4: "Lady Geist", 6: "Abrams",
    7: "Wraith", 8: "McGinnis", 10: "Paradox", 11: "Dynamo", 12: "Kelvin",
    13: "Haze", 14: "Holliday", 15: "Bebop", 16: "Calico", 17: "Grey Talon",
    18: "Mo & Krill", 19: "Shiv", 20: "Ivy", 25: "Warden", 27: "Yamato",
    31: "Lash", 35: "Viscous", 50: "Pocket", 52: "Mirage", 58: "Vyper",
    60: "Sinclair", 63: "Mina", 64: "Drifter", 65: "Venator", 66: "Victor",
    67: "Paige", 69: "The Doorman", 72: "Billy", 76: "Graves", 77: "Apollo",
    79: "Rem", 80: "Silver", 81: "Celeste"
}

MIN_GAMES_THRESHOLD = 0

def load_data():
    if not os.path.exists(INPUT_FILE): 
        print(f"Error: {INPUT_FILE} not found.")
        return None
    with open(INPUT_FILE, 'r') as f:
        content = json.load(f)
        return content.get('data', []) if isinstance(content, dict) else content

def calculate_matrix(data):
    matrix_stats = defaultdict(lambda: {'wins': 0, 'games': 0})
    for entry in data:
        p0, p1, s0, s1, tower_win = entry['p0'], entry['p1'], entry['s0'], entry['s1'], entry['win']
        nw0, nw1 = s0['nw'], s1['nw']
        match_winner = 0 if nw0 > nw1 * 1.10 else (1 if nw1 > nw0 * 1.10 else tower_win)

        for pair_str, team_idx in [(p0, 0), (p1, 1)]:
            h_ids = [int(x) for x in pair_str.split('|')]
            pair_won = 1 if match_winner == team_idx else 0
            h1, h2 = h_ids[0], h_ids[1]
            
            matrix_stats[(h1, h2)]['games'] += 1
            if pair_won: matrix_stats[(h1, h2)]['wins'] += 1
            matrix_stats[(h2, h1)]['games'] += 1
            if pair_won: matrix_stats[(h2, h1)]['wins'] += 1

    flat_data = []
    for (h1_id, h2_id), s in matrix_stats.items():
        if s['games'] >= MIN_GAMES_THRESHOLD:
            flat_data.append({
                'Hero': HERO_NAMES.get(h1_id, f"ID_{h1_id}"),
                'Ally': HERO_NAMES.get(h2_id, f"ID_{h2_id}"),
                'Winrate': round(s['wins'] / s['games'], 3)
            })
    df = pd.DataFrame(flat_data)
    return df.pivot(index='Hero', columns='Ally', values='Winrate')

def export_to_json(data, output_path):
    pair_stats = {}
    for entry in data:
        p0, p1, s0, s1, tower_win = entry['p0'], entry['p1'], entry['s0'], entry['s1'], entry['win']
        nw0, nw1 = s0['nw'], s1['nw']
        winner = 0 if nw0 > nw1 * 1.10 else (1 if nw1 > nw0 * 1.10 else tower_win)

        for pair_str, team_idx in [(p0, 0), (p1, 1)]:
            ids = sorted([int(x) for x in pair_str.split('|')])
            name_key = f"{HERO_NAMES.get(ids[0], ids[0])}|{HERO_NAMES.get(ids[1], ids[1])}"
            if name_key not in pair_stats: pair_stats[name_key] = {'wins': 0, 'games': 0}
            pair_stats[name_key]['games'] += 1
            if winner == team_idx: pair_stats[name_key]['wins'] += 1

    final_json = {key: {"winrate": round(stats['wins']/stats['games'], 4), "matches": stats['games']} 
                  for key, stats in sorted(pair_stats.items())}

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, indent=4, ensure_ascii=False)
    print(f"Synergy JSON saved to {output_path}")

def export_lane_winrates_json(data, output_path):
    hero_lane_data = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'games': 0}))
    for entry in data:
        lane_id = entry.get('l')
        if lane_id is None: continue
        p0, p1, s0, s1, tower_win = entry['p0'], entry['p1'], entry['s0'], entry['s1'], entry['win']
        nw0, nw1 = s0['nw'], s1['nw']
        match_winner = 0 if nw0 > nw1 * 1.10 else (1 if nw1 > nw0 * 1.10 else tower_win)

        for heroes_str, team_idx in [(p0, 0), (p1, 1)]:
            is_winner = (match_winner == team_idx)
            for h_id in [int(x) for x in heroes_str.split('|')]:
                h_name = HERO_NAMES.get(h_id, f"Hero_{h_id}")
                hero_lane_data[h_name][f"lane_{lane_id}"]['games'] += 1
                if is_winner: hero_lane_data[h_name][f"lane_{lane_id}"]['wins'] += 1

    final_json = {h: {l: round(s['wins']/s['games'], 4) for l, s in sorted(lanes.items())} 
                  for h, lanes in sorted(hero_lane_data.items())}

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, indent=4, ensure_ascii=False)
    print(f"Lane Winrates JSON saved to {output_path}")

def main():
    data = load_data()
    if not data: return

    export_to_json(data, SYNERGY_JSON)
    export_lane_winrates_json(data, LANE_STATS_JSON)

    print("Generating Synergy Matrix...")
    matrix_df = calculate_matrix(data)
    
    with pd.ExcelWriter(MATRIX_EXCEL, engine='xlsxwriter') as writer:
        matrix_df.to_excel(writer, sheet_name='Synergy_Matrix')
        ws = writer.sheets['Synergy_Matrix']
        ws.conditional_format(1, 1, len(matrix_df), len(matrix_df.columns), {
            'type': '3_color_scale',
            'min_color': "#F8696B", 'mid_color': "#FFFFFF", 'max_color': "#63BE7B",
            'min_type': 'num', 'min_value': 0.40, 'mid_type': 'num', 'mid_value': 0.50, 'max_type': 'num', 'max_value': 0.60
        })
        ws.set_column(1, len(matrix_df.columns), 10)
        
    print(f"Excel Matrix saved to {MATRIX_EXCEL}")

if __name__ == "__main__":
    main()
