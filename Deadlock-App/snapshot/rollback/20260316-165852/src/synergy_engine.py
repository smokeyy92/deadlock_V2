from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any

import pandas as pd

from utils import ANALYSIS_DIR, PROCESSED_DIR, load_json, safe_div


def compute_synergy_matrix() -> pd.DataFrame:
    matches = load_json(PROCESSED_DIR / "matches.json", default=[])

    wins: dict[tuple[str, str], float] = defaultdict(float)
    games: dict[tuple[str, str], float] = defaultdict(float)

    for match in matches:
        if not isinstance(match, dict):
            continue
        winner = str(match.get("winner") or "").lower()
        team_a = sorted([str(h) for h in match.get("team_a_heroes", [])])
        team_b = sorted([str(h) for h in match.get("team_b_heroes", [])])

        for team_name, team in [("team_a", team_a), ("team_b", team_b)]:
            for hero_a, hero_b in combinations(team, 2):
                key = (hero_a, hero_b)
                games[key] += 1.0
                if winner == team_name:
                    wins[key] += 1.0

    rows = []
    for key in sorted(games.keys()):
        total_games = games[key]
        synergy_score = safe_div(wins[key], total_games)
        rows.append(
            {
                "hero_a": key[0],
                "hero_b": key[1],
                "synergy_score": round(synergy_score, 6),
                "games": int(total_games),
            }
        )

    df = pd.DataFrame(rows, columns=["hero_a", "hero_b", "synergy_score", "games"])
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(ANALYSIS_DIR / "synergy_matrix.csv", index=False)
    return df
