import json
import os
from itertools import combinations, permutations

class SynergyEngine:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.syn_path = os.path.join(base_dir, "data", "lane", "synergy_data.json")
        self.lane_path = os.path.join(base_dir, "data", "lane", "lane_data.json")
        
        self.synergy_data = self._load_json(self.syn_path)
        self.lane_data = self._load_json(self.lane_path)
        self.target_lanes = [1, 3, 4]

    def _load_json(self, path) -> dict:
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def get_pair_synergy(self, h1: str, h2: str) -> float:
        """Get pure synergy winrate between two heroes."""
        pair_key = f"{h1}|{h2}" if h1 < h2 else f"{h2}|{h1}"
        return self.synergy_data.get(pair_key, {}).get("winrate", 0.5) or 0.5

    def get_hero_lane_delta(self, hero: str, lane_id: int) -> float:
        """Calculate how much better/worse a hero performs on a specific lane compared to their average."""
        hero_lanes = self.lane_data.get(hero, {})
        if not hero_lanes:
            return 1.0 # Neutral delta
        
        values = [v for k, v in hero_lanes.items() if isinstance(v, (int, float))]
        if not values: return 1.0
        
        avg_lane_wr = sum(values) / len(values)
        current_lane_wr = hero_lanes.get(f"lane_{lane_id}", avg_lane_wr)
        
        # Delta is a multiplier (e.g., 1.05 for +5% efficiency)
        return current_lane_wr / avg_lane_wr if avg_lane_wr > 0 else 1.0

    def _get_setup_details(self, pairs_with_lanes):
        """Helper to format setup data and calculate final average WR."""
        total_wr = 0
        lane_results = []
        for pair, l_id in pairs_with_lanes:
            # For display, we still use the standard synergy + lane average formula
            syn = self.get_pair_synergy(pair[0], pair[1])
            l1 = self.lane_data.get(pair[0], {}).get(f"lane_{l_id}", 0.5)
            l2 = self.lane_data.get(pair[1], {}).get(f"lane_{l_id}", 0.5)
            actual_wr = (syn + (l1 + l2) / 2) / 2
            
            lane_results.append({"pair": pair, "wr": actual_wr, "lane_id": l_id})
            total_wr += actual_wr
            
        return {"lanes": lane_results, "average_winrate": total_wr / 3}

    def calculate_setup_details(self, setup_dict: dict) -> dict:
        """
        Calculates detailed winrates for a setup, including lane deltas.
        Matches the logic used in automated strategies.
        """
        lane_results = []
        total_wr = 0
        
        for l_id, pair in setup_dict.items():
            if len(pair) == 2:
                # 1. Base Synergy (from synergy_data.json)
                syn = self.get_pair_synergy(pair[0], pair[1])
                
                # 2. Get Lane Deltas (efficiency on this specific lane)
                d1 = self.get_hero_lane_delta(pair[0], l_id)
                d2 = self.get_hero_lane_delta(pair[1], l_id)
                
                # 3. Apply Delta to Synergy (Formula from Strategy 2)
                # We use the average delta of the two heroes
                avg_delta = (d1 + d2) / 2
                lane_wr = syn * avg_delta
                
                lane_results.append({
                    "lane_id": l_id, 
                    "wr": lane_wr, 
                    "pair": pair
                })
                total_wr += lane_wr
            else:
                # Fallback for incomplete lanes
                lane_results.append({"lane_id": l_id, "wr": 0.5, "pair": pair})
                total_wr += 0.5

        return {
            "lanes": lane_results, 
            "average_winrate": total_wr / 3
        }

    def calculate_setup_winrate(self, setup_list: list) -> dict:
        """
        Calculates detailed winrates using the new formula: 
        Winrate = Synergy * ((Delta1 + Delta2) / 2)
        """
        total_wr = 0
        lane_results = []
    
        for pair, l_id in setup_list:
            # 1. Get pure synergy (0.5 if missing)
            syn = self.get_pair_synergy(pair[0], pair[1])
        
            # 2. Get individual lane deltas (1.0 if missing)
            d1 = self.get_hero_lane_delta(pair[0], l_id)
            d2 = self.get_hero_lane_delta(pair[1], l_id)
        
            # 3. Apply the formula
            avg_delta = (d1 + d2) / 2
            actual_wr = syn * avg_delta
        
            lane_results.append({
                "pair": pair, 
                "wr": actual_wr, 
                "lane_id": l_id
            })
            total_wr += actual_wr
        
        return {
            "lanes": lane_results, 
            "average_winrate": total_wr / 3
        }

    def get_top_lane_setups(self, heroes: list[str], top_n: int = 3) -> list[dict]:
        if len(heroes) != 6: return []
    
        # 1. Pre-calculate all 15 unique partitions of 6 heroes into 3 pairs
        partitions = []
        hero_pool = set(heroes)
        for p1 in combinations(heroes, 2):
            rem1 = hero_pool - set(p1)
            for p2 in combinations(list(rem1), 2):
                p3 = tuple(rem1 - set(p2))
                partition = tuple(sorted([tuple(sorted(p1)), tuple(sorted(p2)), tuple(sorted(p3))]))
                if partition not in partitions:
                    partitions.append(partition)

        # 2. Generate all 90 possible unique setups (15 partitions * 6 lane permutations)
        all_possible_setups = []
        for part in partitions:
            for p_perm in permutations(part):
                setup = self.calculate_setup_winrate(zip(p_perm, self.target_lanes))
                # Pre-calculate synergy sum for Strategy 1
                setup['total_synergy'] = sum(self.get_pair_synergy(p[0], p[1]) for p in p_perm)
                # Pre-calculate WR variance for Strategy 3
                wrs = [l['wr'] for l in setup['lanes']]
                setup['variance'] = max(wrs) - min(wrs)
                all_possible_setups.append(setup)

        results = []

        # --- STRATEGY 1: SYNERGY FOCUS ---
        # Maximize pure synergy sum regardless of lane efficiency
        best_syn = max(all_possible_setups, key=lambda x: (x['total_synergy'], x['average_winrate']))
        results.append(best_syn)

        # --- STRATEGY 2: LANE EFFICIENCY (META) ---
        # Maximize total Winrate (Synergy adjusted by Lane Deltas)
        best_eff = max(all_possible_setups, key=lambda x: x['average_winrate'])
        results.append(best_eff)

        # --- STRATEGY 3: BALANCED SETUP ---
        # Find setups where lanes have similar power, but still keeping high average WR
        # We take the top 10% of setups by WR and pick the one with lowest variance
        threshold = best_eff['average_winrate'] * 0.98 # Top performance threshold
        top_tier = [s for s in all_possible_setups if s['average_winrate'] >= threshold]
        best_bal = min(top_tier, key=lambda x: x['variance'])
        results.append(best_bal)

        return results
