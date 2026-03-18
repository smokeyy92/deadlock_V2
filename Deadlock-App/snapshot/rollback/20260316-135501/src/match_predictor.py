from __future__ import annotations

from collections import defaultdict
from itertools import product

import pandas as pd
from pandas.errors import EmptyDataError

from utils import ANALYSIS_DIR, META_DIR, PROCESSED_DIR, load_json, safe_div


def compute_hero_vs_hero_matrix() -> pd.DataFrame:
    matches = load_json(PROCESSED_DIR / "matches.json", default=[])

    wins: dict[tuple[str, str], float] = defaultdict(float)
    games: dict[tuple[str, str], float] = defaultdict(float)

    for match in matches:
        winner = str(match.get("winner") or "").lower()
        team_a = [str(v) for v in match.get("team_a_heroes", [])]
        team_b = [str(v) for v in match.get("team_b_heroes", [])]

        for hero_a, hero_b in product(team_a, team_b):
            key = (hero_a, hero_b)
            games[key] += 1.0
            if winner == "team_a":
                wins[key] += 1.0

            reverse_key = (hero_b, hero_a)
            games[reverse_key] += 1.0
            if winner == "team_b":
                wins[reverse_key] += 1.0

    rows = []
    for key in sorted(games.keys()):
        rows.append(
            {
                "hero_a": key[0],
                "hero_b": key[1],
                "winrate": round(safe_div(wins[key], games[key]), 6),
                "games": int(games[key]),
            }
        )

    df = pd.DataFrame(rows, columns=["hero_a", "hero_b", "winrate", "games"])
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(ANALYSIS_DIR / "hero_vs_hero_matrix.csv", index=False)
    return df


def compute_team_compositions() -> pd.DataFrame:
    matches = load_json(PROCESSED_DIR / "matches.json", default=[])

    wins: dict[str, float] = defaultdict(float)
    games: dict[str, float] = defaultdict(float)

    for match in matches:
        winner = str(match.get("winner") or "").lower()
        team_a = sorted([str(v) for v in match.get("team_a_heroes", [])])
        team_b = sorted([str(v) for v in match.get("team_b_heroes", [])])

        comp_a = "|".join(team_a)
        comp_b = "|".join(team_b)

        if comp_a:
            games[comp_a] += 1.0
            if winner == "team_a":
                wins[comp_a] += 1.0

        if comp_b:
            games[comp_b] += 1.0
            if winner == "team_b":
                wins[comp_b] += 1.0

    rows = []
    for composition in sorted(games.keys()):
        rows.append(
            {
                "composition": composition,
                "winrate": round(safe_div(wins[composition], games[composition]), 6),
                "games": int(games[composition]),
            }
        )

    df = pd.DataFrame(rows, columns=["composition", "winrate", "games"])
    df.to_csv(ANALYSIS_DIR / "team_compositions.csv", index=False)
    return df


def _load_map(path: str, key_col: str, value_col: str) -> dict[str, float]:
    csv_path = ANALYSIS_DIR / path if "analysis" not in path else PROCESSED_DIR.parent / path
    if not csv_path.exists():
        return {}
    try:
        df = pd.read_csv(csv_path)
    except EmptyDataError:
        return {}
    if df.empty:
        return {}
    return dict(zip(df[key_col], df[value_col]))


def predict_matchups() -> pd.DataFrame:
    matches = load_json(PROCESSED_DIR / "matches.json", default=[])

    hero_winrates = _load_map("../meta/hero_winrates.csv", "hero", "winrate")

    synergy_map: dict[tuple[str, str], float] = {}
    synergy_path = ANALYSIS_DIR / "synergy_matrix.csv"
    if synergy_path.exists():
        try:
            synergy_df = pd.read_csv(synergy_path)
        except EmptyDataError:
            synergy_df = pd.DataFrame(columns=["hero_a", "hero_b", "synergy_score"])
        for _, row in synergy_df.iterrows():
            synergy_map[(row["hero_a"], row["hero_b"])] = float(row["synergy_score"])

    counter_map: dict[tuple[str, str], float] = {}
    counter_path = ANALYSIS_DIR / "counter_matrix.csv"
    if counter_path.exists():
        try:
            counter_df = pd.read_csv(counter_path)
        except EmptyDataError:
            counter_df = pd.DataFrame(columns=["hero_a", "hero_b", "counter_score"])
        for _, row in counter_df.iterrows():
            counter_map[(row["hero_a"], row["hero_b"])] = float(row["counter_score"])

    matchup_map: dict[tuple[str, str], float] = {}
    hvh_path = ANALYSIS_DIR / "hero_vs_hero_matrix.csv"
    if hvh_path.exists():
        try:
            hvh_df = pd.read_csv(hvh_path)
        except EmptyDataError:
            hvh_df = pd.DataFrame(columns=["hero_a", "hero_b", "winrate"])
        for _, row in hvh_df.iterrows():
            matchup_map[(row["hero_a"], row["hero_b"])] = float(row["winrate"])

    composition_map = _load_map("team_compositions.csv", "composition", "winrate")

    rows = []
    for match in matches:
        match_id = str(match.get("match_id") or "")
        team_a = [str(v) for v in match.get("team_a_heroes", [])]
        team_b = [str(v) for v in match.get("team_b_heroes", [])]
        winner = str(match.get("winner") or "").lower()

        hero_avg_winrate = safe_div(sum(hero_winrates.get(h, 0.5) for h in team_a), max(len(team_a), 1))

        team_synergy_values = []
        for i in range(len(team_a)):
            for j in range(i + 1, len(team_a)):
                pair = tuple(sorted((team_a[i], team_a[j])))
                team_synergy_values.append(synergy_map.get(pair, 0.5))
        team_synergy = safe_div(sum(team_synergy_values), max(len(team_synergy_values), 1)) if team_synergy_values else 0.5

        counter_values = []
        matchup_values = []
        for hero_a, hero_b in product(team_a, team_b):
            counter_values.append(counter_map.get((hero_a, hero_b), 0.0))
            matchup_values.append(matchup_map.get((hero_a, hero_b), 0.5))
        enemy_counter_score = safe_div(sum(counter_values), max(len(counter_values), 1))
        hero_vs_hero_score = safe_div(sum(matchup_values), max(len(matchup_values), 1))

        composition_key = "|".join(sorted(team_a))
        composition_winrate = composition_map.get(composition_key, 0.5)

        weighted = (
            0.30 * hero_avg_winrate
            + 0.20 * team_synergy
            + 0.20 * enemy_counter_score
            + 0.20 * hero_vs_hero_score
            + 0.10 * composition_winrate
        )

        ranks = match.get("player_ranks", [])
        if isinstance(ranks, list) and ranks:
            avg_rank = sum(float(v) for v in ranks if isinstance(v, (int, float))) / max(len(ranks), 1)
            max_rank = max(float(v) for v in ranks if isinstance(v, (int, float)))
            mmr_weight = safe_div(avg_rank, max_rank) if max_rank else 1.0
        else:
            mmr_weight = 1.0

        team_a_win_probability = round(max(0.0, min(1.0, weighted * mmr_weight)), 6)
        rows.append(
            {
                "match_id": match_id,
                "team_a_win_probability": team_a_win_probability,
                "actual_winner": winner,
            }
        )

    df = pd.DataFrame(rows, columns=["match_id", "team_a_win_probability", "actual_winner"])
    df.to_csv(ANALYSIS_DIR / "matchup_predictions.csv", index=False)
    return df
