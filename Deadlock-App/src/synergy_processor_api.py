import requests
import pandas as pd
import re
import time
from collections import defaultdict

# --- 1. Configuration & Mapping ---
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

TOTAL_POSSIBLE_PAIRS = 703 
LANE_MAP = {1: 1, 4: 3, 6: 4}
API_URL = "https://api.deadlock-api.com/v1/matches/metadata"
OUTPUT_FILE = "deadlock_synergy_api_report.xlsx"

API_PARAMS = {
    "include_info": "true",
    "include_objectives": "true",
    "include_player_info": "true",
    "game_mode": "normal",
    "min_unix_timestamp": "1772902800",
    "min_average_badge": "104",
    "is_low_pri_pool": "false",
    "is_new_player_pool": "false",
    "order_by": "match_id",
    "order_direction": "desc",
    "limit": "5000"
}

def process_match_batch(matches):
    """Processes matches to extract both Synergy (allies) and Matchups (opponents)."""
    synergy_records = []
    matchup_records = []
    
    for match in matches:
        objectives = match.get("objectives", [])
        players = match.get("players", [])
        
        lane_times = {1: {"Team0": 99999, "Team1": 99999}, 
                      3: {"Team0": 99999, "Team1": 99999}, 
                      4: {"Team0": 99999, "Team1": 99999}}
        
        for obj in objectives:
            name = str(obj.get("team_objective", ""))
            time_destroyed = int(obj.get("destroyed_time_s", 0))
            if "Tier1Lane" in name and time_destroyed > 0:
                match_digit = re.search(r'Lane(\d+)', name)
                if match_digit:
                    l_num = int(match_digit.group(1))
                    team_raw = obj.get("team")
                    team = f"Team{team_raw}" if isinstance(team_raw, int) else str(team_raw)
                    if l_num in lane_times:
                        lane_times[l_num][team] = time_destroyed

        lane_winners = {}
        for l_id in [1, 3, 4]:
            t0, t1 = lane_times[l_id]["Team0"], lane_times[l_id]["Team1"]
            if t0 == 99999 and t1 == 99999:
                lane_winners[l_id] = None
            else:
                lane_winners[l_id] = "Team1" if t0 < t1 else "Team0"

        lane_groups = defaultdict(lambda: {"Team0": [], "Team1": []})
        for p in players:
            target_lane = LANE_MAP.get(p.get("assigned_lane"))
            if target_lane:
                team_raw = p.get("team")
                team_key = f"Team{team_raw}" if isinstance(team_raw, int) else ("Team0" if "Team0" in str(team_raw) else "Team1")
                h_name = HERO_NAMES.get(p.get("hero_id"), f"Hero_{p.get('hero_id')}")
                lane_groups[target_lane][team_key].append(h_name)

        for l_id in [1, 3, 4]:
            winner = lane_winners.get(l_id)
            if not winner: continue
            
            t0_heroes = lane_groups[l_id]["Team0"]
            t1_heroes = lane_groups[l_id]["Team1"]

            # 1. Extract Synergy (Allies) - only for duos
            for t_name, heroes in lane_groups[l_id].items():
                if len(heroes) == 2:
                    h1, h2 = sorted(heroes)
                    synergy_records.append({'Hero1': h1, 'Hero2': h2, 'Win': 1 if t_name == winner else 0})

            # 2. Extract Matchups (Opponents) - any combination
            if t0_heroes and t1_heroes:
                for h0 in t0_heroes:
                    for h1 in t1_heroes:
                        # Record for Hero from Team0 vs Hero from Team1
                        matchup_records.append({'Hero': h0, 'Opponent': h1, 'Win': 1 if winner == "Team0" else 0})
                        # Record for Hero from Team1 vs Hero from Team0
                        matchup_records.append({'Hero': h1, 'Opponent': h0, 'Win': 1 if winner == "Team1" else 0})
                        
    return synergy_records, matchup_records

def main():
    all_synergy = []
    all_matchups = []
    current_max_id = "9999999999999"
    iteration = 1
    
    print(f"Starting cyclic data collection...")

    while True:
        API_PARAMS["max_match_id"] = current_max_id
        print(f"Iteration {iteration}: Fetching below ID {current_max_id}...")
        
        try:
            response = requests.get(API_URL, params=API_PARAMS, timeout=60)
            response.raise_for_status()
            matches = response.json()
        except Exception as e:
            print(f"  [ERROR] Stopped: {e}")
            break

        if not matches: break

        syn_batch, match_batch = process_match_batch(matches)
        all_synergy.extend(syn_batch)
        all_matchups.extend(match_batch)
        
        # Coverage calculation for Synergy
        if all_synergy:
            counts = pd.DataFrame(all_synergy).groupby(['Hero1', 'Hero2']).size()
            coverage = ( (counts >= 100).sum() / TOTAL_POSSIBLE_PAIRS ) * 100
            print(f"  [PROGRESS] Synergy Coverage: {coverage:.1f}%")
        
        match_ids = [int(m.get("match_id")) for m in matches if m.get("match_id")]
        if not match_ids or len(matches) < 1000: break
        current_max_id = str(min(match_ids) - 1)
        iteration += 1

    if not all_synergy:
        print("No data collected."); return

    # --- Processing Synergy Data ---
    df_syn = pd.DataFrame(all_synergy)
    stats_syn = df_syn.groupby(['Hero1', 'Hero2'])['Win'].agg(['mean', 'count']).reset_index()
    mirrored_syn = pd.concat([
        stats_syn.rename(columns={'Hero1': 'Hero', 'Hero2': 'Ally', 'mean': 'WR', 'count': 'Cnt'}),
        stats_syn.rename(columns={'Hero1': 'Ally', 'Hero2': 'Hero', 'mean': 'WR', 'count': 'Cnt'})
    ])

    # --- Processing Matchup Data ---
    df_match = pd.DataFrame(all_matchups)
    stats_match = df_match.groupby(['Hero', 'Opponent'])['Win'].agg(['mean', 'count']).reset_index()

    # --- Excel Export ---
    with pd.ExcelWriter(OUTPUT_FILE, engine='xlsxwriter') as writer:
        # Sheet 1: Synergy Winrates (Threshold applied)
        mirrored_syn.loc[mirrored_syn['Cnt'] < 100, 'WR'] = None
        mirrored_syn.pivot(index='Hero', columns='Ally', values='WR').to_excel(writer, sheet_name='Synergy_Winrates')
        
        # Sheet 2: Matchup Winrates (Threshold applied)
        stats_match_filtered = stats_match.copy()
        stats_match_filtered.loc[stats_match_filtered['count'] < 100, 'mean'] = None
        stats_match_filtered.pivot(index='Hero', columns='Opponent', values='mean').to_excel(writer, sheet_name='Matchup_Winrates')

        # Sheet 3: Match Counts (Synergy)
        mirrored_syn.pivot(index='Hero', columns='Ally', values='Cnt').to_excel(writer, sheet_name='Synergy_Counts')

        # Formatting
        for sheet_name in ['Synergy_Winrates', 'Matchup_Winrates']:
            ws = writer.sheets[sheet_name]
            ws.conditional_format(1, 1, 100, 100, {
                'type': '3_color_scale', 
                'min_color': "#F8696B", 'mid_color': "#FFFFFF", 'max_color': "#63BE7B",
                'min_type': 'num', 'min_value': 0.35, 'mid_type': 'num', 'mid_value': 0.50, 'max_type': 'num', 'max_value': 0.65
            })

        ws_cnt = writer.sheets['Synergy_Counts']
        ws_cnt.conditional_format(1, 1, 100, 100, {
            'type': '3_color_scale',
            'min_color': "#FFEB84", 'mid_color': "#81D4FA", 'max_color': "#0D47A1",
            'min_type': 'num', 'min_value': 0, 'mid_type': 'num', 'mid_value': 100, 'max_type': 'num', 'max_value': 500
        })

    print(f"\nSUCCESS: Report with Synergy and Matchups saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()