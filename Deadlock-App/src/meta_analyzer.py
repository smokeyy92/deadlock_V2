from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError

from utils import META_DIR, PROCESSED_DIR, load_json, safe_div


def compute_pick_and_winrates() -> tuple[pd.DataFrame, pd.DataFrame]:
    matches = load_json(PROCESSED_DIR / "matches.json", default=[])

    picks: dict[str, float] = defaultdict(float)
    wins: dict[str, float] = defaultdict(float)
    total_match_sides = 0.0

    for match in matches:
        if not isinstance(match, dict):
            continue
        winner = str(match.get("winner") or "").lower()
        team_a = [str(h) for h in match.get("team_a_heroes", [])]
        team_b = [str(h) for h in match.get("team_b_heroes", [])]

        total_match_sides += 2.0
        for hero in team_a:
            picks[hero] += 1.0
            if winner == "team_a":
                wins[hero] += 1.0

        for hero in team_b:
            picks[hero] += 1.0
            if winner == "team_b":
                wins[hero] += 1.0

    heroes = sorted(picks.keys())
    pick_df = pd.DataFrame(
        [
            {
                "hero": hero,
                "pickrate": round(safe_div(picks[hero], total_match_sides), 6),
            }
            for hero in heroes
        ],
        columns=["hero", "pickrate"],
    )
    win_df = pd.DataFrame(
        [
            {
                "hero": hero,
                "winrate": round(safe_div(wins[hero], picks[hero]), 6),
            }
            for hero in heroes
        ],
        columns=["hero", "winrate"],
    )

    META_DIR.mkdir(parents=True, exist_ok=True)
    pick_df.to_csv(META_DIR / "hero_pickrates.csv", index=False)
    win_df.to_csv(META_DIR / "hero_winrates.csv", index=False)
    return pick_df, win_df


def compute_meta_scores() -> pd.DataFrame:
    pick_df, win_df = compute_pick_and_winrates()

    synergy_path = PROCESSED_DIR.parent / "analysis" / "synergy_matrix.csv"
    counter_path = PROCESSED_DIR.parent / "analysis" / "counter_matrix.csv"

    if synergy_path.exists():
        try:
            synergy_df = pd.read_csv(synergy_path)
        except EmptyDataError:
            synergy_df = pd.DataFrame(columns=["hero_a", "synergy_score"])
        synergy_scores = synergy_df.groupby("hero_a")["synergy_score"].mean().to_dict()
    else:
        synergy_scores = {}

    if counter_path.exists():
        try:
            counter_df = pd.read_csv(counter_path)
        except EmptyDataError:
            counter_df = pd.DataFrame(columns=["hero_a", "counter_score"])
        counter_scores = counter_df.groupby("hero_a")["counter_score"].mean().to_dict()
    else:
        counter_scores = {}

    merged = pick_df.merge(win_df, on="hero", how="outer").fillna(0.0)
    merged["synergy_score"] = merged["hero"].map(synergy_scores).fillna(0.0)
    merged["counter_score"] = merged["hero"].map(counter_scores).fillna(0.0)
    merged["meta_score"] = (
        merged["winrate"] * 0.5
        + merged["pickrate"] * 0.25
        + merged["synergy_score"] * 0.15
        + merged["counter_score"] * 0.10
    )

    result = merged.sort_values("meta_score", ascending=False)
    result.to_csv(META_DIR / "hero_meta_scores.csv", index=False)
    return result
