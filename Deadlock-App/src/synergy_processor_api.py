import requests
import pandas as pd
import re
import time
from collections import defaultdict
import json
import os

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
    """
    Processes matches to extract Synergy, Matchups, Lane Winrates, and Snowball Potential.
    Returns: synergy_records, matchup_records, lane_records, snowball_records
    """
    synergy_records = []
    matchup_records = []
    lane_records = []
    snowball_records = []
    
    for match in matches:
        objectives = match.get("objectives", [])
        players = match.get("players", [])
        # Get the match winner (usually 0 or 1)
        match_winner_team = match.get("winning_team") 
        
        # 1. Track tower destruction times
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
                    # Normalize team name to "Team0" or "Team1"
                    team = f"Team{team_raw}" if isinstance(team_raw, int) else str(team_raw)
                    if l_num in lane_times:
                        lane_times[l_num][team] = time_destroyed

        # 2. Determine lane winners (whoever lost tower later wins the lane)
        lane_winners = {}
        for l_id in [1, 3, 4]:
            t0, t1 = lane_times[l_id]["Team0"], lane_times[l_id]["Team1"]
            if t0 == 99999 and t1 == 99999:
                lane_winners[l_id] = None
            else:
                lane_winners[l_id] = "Team1" if t0 < t1 else "Team0"

        # 3. Group players and handle Snowball Logic
        lane_groups = defaultdict(lambda: {"Team0": [], "Team1": []})
        for p in players:
            target_lane = LANE_MAP.get(p.get("assigned_lane"))
            if target_lane:
                team_raw = p.get("team")
                # Fix for "TeamTeam0" error: check if prefix already exists
                if isinstance(team_raw, int):
                    team_key = f"Team{team_raw}"
                else:
                    team_key = str(team_raw) if "Team" in str(team_raw) else f"Team{team_raw}"
                
                h_id = p.get("hero_id")
                h_name = HERO_NAMES.get(h_id, f"Hero_{h_id}")
                lane_groups[target_lane][team_key].append(h_name)

                # --- Snowball Calculation ---
                l_winner = lane_winners.get(target_lane)
                if l_winner and l_winner == team_key:
                    # Match winner from API is a string like "Team0" or "Team1"
                    # We compare it directly with our team_key ("Team0"/"Team1")
                    is_match_win = 1 if team_key == match_winner_team else 0
                    
                    # Log for debugging if needed: 
                    # print(f"Hero {h_name} won lane. Team: {team_key}, Winner: {match_winner_team} -> {is_match_win}")
                    
                    snowball_records.append({'Hero': h_name, 'MatchWin': is_match_win})


        # 4. Extract Winrates and Synergy
        for l_id in [1, 3, 4]:
            winner = lane_winners.get(l_id)
            if not winner: continue
            
            t0_heroes = lane_groups[l_id]["Team0"]
            t1_heroes = lane_groups[l_id]["Team1"]

            # Lane records (Individual WR on lane)
            for team_name, heroes in lane_groups[l_id].items():
                is_win = 1 if team_name == winner else 0
                for h_name in heroes:
                    lane_records.append({'Hero': h_name, 'Lane': l_id, 'Win': is_win})

                # Synergy records (Duo winrates)
                if len(heroes) == 2:
                    h1, h2 = sorted(heroes)
                    synergy_records.append({'Hero1': h1, 'Hero2': h2, 'Win': is_win})

            # Matchup records (Vs opponents)
            if t0_heroes and t1_heroes:
                for h0 in t0_heroes:
                    for h1 in t1_heroes:
                        matchup_records.append({'Hero': h0, 'Opponent': h1, 'Win': 1 if winner == "Team0" else 0})
                        matchup_records.append({'Hero': h1, 'Opponent': h0, 'Win': 1 if winner == "Team1" else 0})
                        
    return synergy_records, matchup_records, lane_records, snowball_records

def main():
    all_synergy = []
    all_matchups = []
    all_lanes = []
    all_snowball = []
    current_max_id = "9999999999999"
    iteration = 1
    
    print(f"Starting cyclic data collection...")

    while True:
        API_PARAMS["max_match_id"] = current_max_id
        print(f"Iteration {iteration}: Fetching below ID {current_max_id}...")
        
        try:
            response = requests.get(API_URL, params=API_PARAMS, timeout=60)
            if response.status_code == 404:
                print(f"  [INFO] No more historical data available (ID: {current_max_id}).")
                break
            response.raise_for_status()
            matches = response.json()
        except Exception as e:
            print(f"  [ERROR] Stopped: {e}")
            break

        if not matches: break

        syn_batch, match_batch, lane_batch, snowball_batch = process_match_batch(matches)
        all_synergy.extend(syn_batch)
        all_matchups.extend(match_batch)
        all_lanes.extend(lane_batch)
        all_snowball.extend(snowball_batch)
        
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

    # --- Processing Data ---
    df_syn = pd.DataFrame(all_synergy)
    stats_syn = df_syn.groupby(['Hero1', 'Hero2'])['Win'].agg(['mean', 'count']).reset_index()
    mirrored_syn = pd.concat([
        stats_syn.rename(columns={'Hero1': 'Hero', 'Hero2': 'Ally', 'mean': 'WR', 'count': 'Cnt'}),
        stats_syn.rename(columns={'Hero1': 'Ally', 'Hero2': 'Hero', 'mean': 'WR', 'count': 'Cnt'})
    ])

    df_match = pd.DataFrame(all_matchups)
    stats_match = df_match.groupby(['Hero', 'Opponent'])['Win'].agg(['mean', 'count']).reset_index()

    # --- NEW: Processing Lane Stats ---
    df_lane = pd.DataFrame(all_lanes)
    stats_lane = df_lane.groupby(['Hero', 'Lane'])['Win'].agg(['mean', 'count']).reset_index()
    lane_pivot = stats_lane.pivot(index='Hero', columns='Lane', values='mean')

    # --- Excel Export ---
    with pd.ExcelWriter(OUTPUT_FILE, engine='xlsxwriter') as writer:
        mirrored_syn.loc[mirrored_syn['Cnt'] < 100, 'WR'] = None
        mirrored_syn.pivot(index='Hero', columns='Ally', values='WR').to_excel(writer, sheet_name='Synergy_Winrates')
        
        stats_match_filtered = stats_match.copy()
        stats_match_filtered.loc[stats_match_filtered['count'] < 100, 'mean'] = None
        stats_match_filtered.pivot(index='Hero', columns='Opponent', values='mean').to_excel(writer, sheet_name='Matchup_Winrates')

        mirrored_syn.pivot(index='Hero', columns='Ally', values='Cnt').to_excel(writer, sheet_name='Synergy_Counts')
        
        # New Sheet: Lane Winrates
        lane_pivot.to_excel(writer, sheet_name='Lane_Winrates')

        # Formatting
        for sheet_name in ['Synergy_Winrates', 'Matchup_Winrates', 'Lane_Winrates']:
            ws = writer.sheets[sheet_name]
            ws.conditional_format(1, 1, 100, 100, {
                'type': '3_color_scale', 
                'min_color': "#F8696B", 'mid_color': "#FFFFFF", 'max_color': "#63BE7B",
                'min_type': 'num', 'min_value': 0.40, 'mid_type': 'num', 'mid_value': 0.50, 'max_type': 'num', 'max_value': 0.60
            })

    # --- JSON Export ---
    os.makedirs("data", exist_ok=True)
    
    # 1. Synergy JSON
    json_stats = {}
    for _, row in stats_syn.iterrows():
        pair_key = f"{row['Hero1']}|{row['Hero2']}"
        json_stats[pair_key] = {"winrate": round(float(row['mean']), 4) if row['count'] >= 100 else 0.0, "matches": int(row['count'])}
    
    with open(os.path.join("data", "synergy_data.json"), "w", encoding="utf-8") as f:
        json.dump(json_stats, f, indent=4, ensure_ascii=False)

    # 2. Lane JSON
    lane_json = {}
    for _, row in stats_lane.iterrows():
        hero = row['Hero']
        if hero not in lane_json: lane_json[hero] = {}
        lane_json[hero][f"lane_{int(row['Lane'])}"] = round(float(row['mean']), 4)

    with open(os.path.join("data", "lane_data.json"), "w", encoding="utf-8") as f:
        json.dump(lane_json, f, indent=4, ensure_ascii=False)

    print(f"\nSUCCESS: Reports saved. Lane data included.")

    # --- Processing Snowball Data ---
    if all_snowball:
        df_snowball = pd.DataFrame(all_snowball)
        
        # Double check if the column exists to prevent KeyError
        if 'Hero' in df_snowball.columns:
            snowball_stats = df_snowball.groupby('Hero')['MatchWin'].agg(['mean', 'count']).reset_index()
            snowball_stats.columns = ['Hero', 'Snowball_WR', 'Lanes_Won_Count']
            snowball_stats = snowball_stats.sort_values(by='Snowball_WR', ascending=False)
            
            # --- JSON Export for Snowball Potential ---
            MIN_LANE_WINS = 50
            snowball_json_stats = {}

            for _, row in snowball_stats.iterrows():
                hero = row['Hero']
                count = int(row['Lanes_Won_Count'])
                
                # Check threshold for data quality
                if count >= MIN_LANE_WINS:
                    snowball_json_stats[hero] = {
                        "snowball_wr": round(float(row['Snowball_WR']), 4),
                        "lanes_won": count
                    }
                else:
                    snowball_json_stats[hero] = {
                        "snowball_wr": 0.0,
                        "lanes_won": count
                    }

            # Save Snowball JSON
            os.makedirs("data", exist_ok=True)
            snowball_path = os.path.join("data", "snowball_data.json")
            with open(snowball_path, "w", encoding="utf-8") as f:
                json.dump(snowball_json_stats, f, indent=4, ensure_ascii=False)
            
            print(f"SUCCESS: Snowball data exported to {snowball_path}")
            
            # --- Excel Export (Add sheet only if data exists) ---
            # If you are using the same Excel writer as before, make sure it's within the 'with' block
            # snowball_stats.to_excel(writer, sheet_name='Snowball_Potential', index=False)
        else:
            print("WARNING: Snowball data collected but format is incorrect.")
    else:
        print("WARNING: No snowball data collected (list is empty).")

if __name__ == "__main__":
    main()
