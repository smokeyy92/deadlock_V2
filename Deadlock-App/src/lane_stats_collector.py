import requests
import json
import re
import time
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR) 
DATA_LANE_DIR = os.path.join(ROOT_DIR, "data", "lane")

os.makedirs(DATA_LANE_DIR, exist_ok=True)

LANES_FILE = os.path.join(DATA_LANE_DIR, "lane_stats.json")

API_URL = "https://api.deadlock-api.com/v1/matches/metadata"
LANE_MAP = {1: 1, 4: 3, 6: 4}

API_PARAMS = {
    "include_info": "true",
    "include_objectives": "true",
    "include_player_info": "true",
    "include_player_stats": "true",
    "game_mode": "normal",
    "min_unix_timestamp": "1722902800",
    "min_average_badge": "104",
    "is_low_pri_pool": "false",
    "is_new_player_pool": "false",
    "order_by": "match_id",
    "order_direction": "desc",
    "limit": "100"
}

def process_match_batch(matches):
    batch_lanes = []
    for match in matches:
        m_id = match.get("match_id")
        print(f"    Match: {m_id}")
        
        objectives = match.get("objectives", [])
        players = match.get("players", [])
        
        # 1. Tower Logic
        lane_times = {1: {"Team0": 99999, "Team1": 99999}, 3: {"Team0": 99999, "Team1": 99999}, 4: {"Team0": 99999, "Team1": 99999}}
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
            lane_winners[l_id] = None if (t0 == 99999 and t1 == 99999) else (0 if t0 > t1 else 1)

        # 2. Metrics Logic (9-min)
        lane_groups = defaultdict(lambda: {"Team0": [], "Team1": []})
        for p in players:
            target_lane = LANE_MAP.get(p.get("assigned_lane"))
            if not target_lane: continue
            h_id, team_raw = p.get("hero_id"), p.get("team")
            team_key = f"Team{team_raw}" if isinstance(team_raw, int) else ("Team0" if "Team0" in str(team_raw) else "Team1")
            
            m9 = {"k": 0, "dmg": 0, "nw": 0}
            for entry in p.get("stats", []):
                if entry.get("time_stamp_s") == 540:
                    m9 = {"k": entry.get("kills", 0), "dmg": entry.get("player_damage", 0), "nw": entry.get("net_worth", 0)}
                    break
            lane_groups[target_lane][team_key].append({"id": h_id, "m9": m9})

        # 3. Aggregation
        for l_id, teams in lane_groups.items():
            t0, t1 = teams.get("Team0", []), teams.get("Team1", [])
            winner_idx = lane_winners.get(l_id)
            if len(t0) == 2 and len(t1) == 2 and winner_idx is not None:
                h0, h1 = sorted(t0, key=lambda x: x["id"]), sorted(t1, key=lambda x: x["id"])
                batch_lanes.append({
                    "l": l_id,
                    "p0": f"{h0[0]['id']}|{h0[1]['id']}",
                    "p1": f"{h1[0]['id']}|{h1[1]['id']}",
                    "s0": {"nw": h0[0]['m9']['nw'] + h0[1]['m9']['nw'], "dmg": h0[0]['m9']['dmg'] + h0[1]['m9']['dmg'], "k": h0[0]['m9']['k'] + h0[1]['m9']['k']},
                    "s1": {"nw": h1[0]['m9']['nw'] + h1[1]['m9']['nw'], "dmg": h1[0]['m9']['dmg'] + h1[1]['m9']['dmg'], "k": h1[0]['m9']['k'] + h1[1]['m9']['k']},
                    "win": winner_idx
                })
    return batch_lanes

STOP_MATCH_ID = 65196005

def main():
    storage = {"last_match_id": "9999999999999", "data": []}

    if os.path.exists(LANES_FILE):
        print(f"Loading existing data from {LANES_FILE}...")
        with open(LANES_FILE, 'r') as f:
            storage = json.load(f)

    print(f"Starting Collection. Target Stop ID: {STOP_MATCH_ID}")

    while True:
        API_PARAMS["max_match_id"] = storage["last_match_id"]
        try:
            resp = requests.get(API_URL, params=API_PARAMS, timeout=30)
            resp.raise_for_status()
            matches = resp.json()
            
            if not matches: 
                print("No more matches returned from API.")
                break

            new_lanes = process_match_batch(matches)
            storage["data"].extend(new_lanes)
            
            match_ids = [int(m["match_id"]) for m in matches if "match_id" in m]
            min_id = min(match_ids)
            storage["last_match_id"] = str(min_id - 1)

            with open(LANES_FILE, 'w') as f:
                json.dump(storage, f)
            
            print(f"  [Batch] Min ID in batch: {min_id}. Total records: {len(storage['data'])}")

            if min_id <= STOP_MATCH_ID:
                print(f"Target Match ID {STOP_MATCH_ID} reached. Stopping.")
                break

            time.sleep(0.5)
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    main()
