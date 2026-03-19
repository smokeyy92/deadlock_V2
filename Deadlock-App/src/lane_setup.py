import json
import os
from itertools import combinations, permutations

class SynergyEngine:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.syn_path = os.path.join(base_dir, "data", "synergy_data.json")
        self.lane_path = os.path.join(base_dir, "data", "lane_data.json")
        self.snowball_path = os.path.join(base_dir, "data", "snowball_data.json")
        
        self.synergy_data = self._load_json(self.syn_path)
        self.lane_data = self._load_json(self.lane_path)
        self.snowball_data = self._load_json(self.snowball_path)
        self.target_lanes = [1, 3, 4]

    def is_snowball_hero(self, hero_name: str) -> bool:
        """Checks if a hero is a high-impact snowballer (WR > 60% after winning lane)."""
        data = self.snowball_data.get(hero_name, {})
        # Threshold: 60% snowball winrate and at least 50 matches
        print(f"Checking {hero_name}: WR is {data.get("snowball_wr", 0)}")
        return data.get("snowball_wr", 0) > 0.60

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

    def get_top_lane_setups(self, heroes: list[str], top_n: int = 3) -> list[dict]:
        if len(heroes) != 6: return []
        
        # Pre-calculate all unique partitions of 6 heroes into 3 pairs
        partitions = []
        hero_pool = set(heroes)
        for p1 in combinations(heroes, 2):
            rem1 = hero_pool - set(p1)
            for p2 in combinations(list(rem1), 2):
                p3 = tuple(rem1 - set(p2))
                partition = tuple(sorted([tuple(sorted(p1)), tuple(sorted(p2)), tuple(sorted(p3))]))
                if partition not in partitions:
                    partitions.append(partition)

        results = []

        # --- STRATEGY 1: BEST SYNERGY ---
        # Find partition with highest combined pure synergy
        best_syn_partition = max(partitions, key=lambda part: sum(self.get_pair_synergy(p[0], p[1]) for p in part))
        # Find best lane distribution for these specific pairs
        best_dist = None
        max_dist_wr = -1
        for p_perm in permutations(best_syn_partition):
            setup = self._get_setup_details(zip(p_perm, self.target_lanes))
            if setup["average_winrate"] > max_dist_wr:
                max_dist_wr = setup["average_winrate"]
                best_dist = setup
        results.append(best_dist)

        # --- STRATEGY 2: BEST LANE EFFICIENCY (DELTA) ---
        all_possible_setups = []
        for part in partitions:
            for p_perm in permutations(part):
                score = 0
                for i, pair in enumerate(p_perm):
                    l_id = self.target_lanes[i]
                    syn = self.get_pair_synergy(pair[0], pair[1])
                    d1 = self.get_hero_lane_delta(pair[0], l_id)
                    d2 = self.get_hero_lane_delta(pair[1], l_id)
                    score += syn * ((d1 + d2) / 2)
                
                setup = self._get_setup_details(zip(p_perm, self.target_lanes))
                setup['score'] = score
                all_possible_setups.append(setup)
        
        best_lane_setup = max(all_possible_setups, key=lambda x: x['score'])
        results.append(best_lane_setup)

        # --- STRATEGY 3: BALANCED LANES ---
        # Same as Strategy 2, but minimize WR difference between lanes
        # Criteria: Total WR >= (Best Lane WR - 1%)
        threshold = best_lane_setup['average_winrate'] - 0.01
        valid_setups = [s for s in all_possible_setups if s['average_winrate'] >= threshold]
        
        def get_variance(setup):
            wrs = [l['wr'] for l in setup['lanes']]
            return max(wrs) - min(wrs)

        balanced_setup = min(valid_setups, key=get_variance)
        results.append(balanced_setup)

        return results
