import json
import os
from itertools import combinations, permutations

class SynergyEngine:
    def __init__(self):
        # Setup absolute paths to data files
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.syn_path = os.path.join(base_dir, "data", "synergy_data.json")
        self.lane_path = os.path.join(base_dir, "data", "lane_data.json")
        
        # Load datasets
        self.synergy_data = self._load_json(self.syn_path)
        self.lane_data = self._load_json(self.lane_path)

    def _load_json(self, path) -> dict:
        """Helper to safely load JSON data from disk."""
        if not os.path.exists(path):
            print(f"[SynergyEngine] Warning: File not found at {path}")
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[SynergyEngine] Error loading JSON: {e}")
            return {}

    def get_calculated_wr(self, h1: str, h2: str, lane_id: int) -> float:
        """
        Calculates winrate based on: 
        (Pair Synergy + Average of individual hero performance on specific lane) / 2.
        """
        # 1. Synergy (Allies)
        pair = sorted([h1, h2])
        pair_key = f"{pair[0]}|{pair[1]}"
        # If synergy data is missing or low sample size (0.0), assume neutral 0.5
        syn_wr = self.synergy_data.get(pair_key, {}).get("winrate", 0.5)
        if syn_wr == 0: syn_wr = 0.5 

        # 2. Individual Lane Performance (Lane 1, 3, or 4)
        l_key = f"lane_{lane_id}"
        h1_l_wr = self.lane_data.get(h1, {}).get(l_key, 0.5)
        h2_l_wr = self.lane_data.get(h2, {}).get(l_key, 0.5)
        lane_perf = (h1_l_wr + h2_l_wr) / 2

        # Combine synergy and lane efficiency
        return (syn_wr + lane_perf) / 2

    def get_top_lane_setups(self, heroes: list[str], top_n: int = 3) -> list[dict]:
        """
        Iterates through all possible lane assignments and returns the best configurations.
        """
        if len(heroes) != 6:
            return []

        all_configs = []
        target_lanes = [1, 3, 4]
        hero_pool = set(heroes)

        # Step 1: Partition 6 heroes into 3 unique pairs (15 possible combinations)
        for p1 in combinations(heroes, 2):
            rem1 = hero_pool - set(p1)
            for p2 in combinations(list(rem1), 2):
                p3 = tuple(rem1 - set(p2))
                
                current_pairs = [tuple(sorted(p1)), tuple(sorted(p2)), tuple(sorted(p3))]
                
                # Step 2: Test every permutation of these 3 pairs across Lanes 1, 3, and 4
                for permutation in permutations(current_pairs):
                    setup_lanes = []
                    total_wr = 0
                    
                    for i, pair in enumerate(permutation):
                        l_id = target_lanes[i]
                        wr = self.get_calculated_wr(pair[0], pair[1], l_id)
                        setup_lanes.append({
                            "pair": pair, 
                            "wr": wr, 
                            "lane_id": l_id
                        })
                        total_wr += wr
                    
                    all_configs.append({
                        "lanes": setup_lanes,
                        "average_winrate": total_wr / 3
                    })

        # Sort results by winrate descending
        all_configs.sort(key=lambda x: x["average_winrate"], reverse=True)
        
        # Step 3: Extract top N unique setups
        unique_results = []
        seen_signatures = set()
        
        for config in all_configs:
            # Signature: unique set of (lane_id, pair) to avoid duplicates
            sig = tuple(sorted([(l["lane_id"], l["pair"]) for l in config["lanes"]]))
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                unique_results.append(config)
            
            if len(unique_results) >= top_n:
                break
                
        return unique_results
