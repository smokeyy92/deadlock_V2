from __future__ import annotations

from collections import Counter

import pandas as pd

from utils import ANALYSIS_DIR, PROCESSED_DIR, load_json


def score_team(team: list[str]) -> float:
    if not team:
        return 0.0

    role_bias = Counter()
    for hero in team:
        hero_name = str(hero).lower()
        if hero_name in {"abrams", "kelvin", "warden", "viscous"}:
            role_bias["tank"] += 1
        elif hero_name in {"ivy", "dynamo", "mcginnis", "pocket"}:
            role_bias["support"] += 1
        elif hero_name in {"wraith", "shiv", "haze", "infernus"}:
            role_bias["carry"] += 1
        else:
            role_bias["flex"] += 1

    diversity_bonus = min(len(role_bias), 5) / 5.0
    balance_penalty = max(role_bias.values()) / len(team)
    score = (0.7 * diversity_bonus + 0.3 * (1.0 - balance_penalty)) * 100.0
    return round(max(0.0, min(100.0, score)), 3)


def analyze_teams() -> pd.DataFrame:
    matches = load_json(PROCESSED_DIR / "matches.json", default=[])

    rows: list[dict[str, object]] = []
    for match in matches:
        team_a = [str(v) for v in match.get("team_a_heroes", [])]
        team_b = [str(v) for v in match.get("team_b_heroes", [])]
        rows.append(
            {
                "match_id": str(match.get("match_id") or ""),
                "team_a_strength_score": score_team(team_a),
                "team_b_strength_score": score_team(team_b),
            }
        )

    df = pd.DataFrame(rows, columns=["match_id", "team_a_strength_score", "team_b_strength_score"])
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(ANALYSIS_DIR / "team_scores.csv", index=False)
    return df
