from __future__ import annotations

from itertools import product

import pandas as pd
from pandas.errors import EmptyDataError

from utils import ANALYSIS_DIR, META_DIR, PROCESSED_DIR, load_json


def recommend_picks(ally_picks: list[str], enemy_picks: list[str], top_n: int | None = 5) -> pd.DataFrame:
    heroes = load_json(PROCESSED_DIR / "heroes.json", default=[])
    pool = [str(hero.get("name") or hero.get("hero_id") or "") for hero in heroes if isinstance(hero, dict)]
    pool = sorted({h for h in pool if h and h not in ally_picks and h not in enemy_picks})
    key_by_name: dict[str, str] = {}
    for hero in heroes:
        if not isinstance(hero, dict):
            continue
        name = str(hero.get("name") or "").strip()
        if not name:
            continue
        key_by_name[name] = str(hero.get("hero_id") or hero.get("id") or name)

    meta_path = META_DIR / "hero_meta_scores.csv"
    if meta_path.exists():
        try:
            meta_df = pd.read_csv(meta_path)
        except EmptyDataError:
            meta_df = pd.DataFrame(columns=["hero", "meta_score"])
        meta_df["hero"] = meta_df["hero"].astype(str)
        meta_scores = dict(zip(meta_df["hero"], meta_df["meta_score"]))
    else:
        meta_scores = {}

    synergy_path = ANALYSIS_DIR / "synergy_matrix.csv"
    synergy_map: dict[tuple[str, str], float] = {}
    if synergy_path.exists():
        try:
            synergy_df = pd.read_csv(synergy_path)
        except EmptyDataError:
            synergy_df = pd.DataFrame(columns=["hero_a", "hero_b", "synergy_score"])
        for _, row in synergy_df.iterrows():
            key = tuple(sorted((str(row["hero_a"]), str(row["hero_b"]))))
            synergy_map[key] = float(row["synergy_score"])

    counter_path = ANALYSIS_DIR / "counter_matrix.csv"
    counter_map: dict[tuple[str, str], float] = {}
    if counter_path.exists():
        try:
            counter_df = pd.read_csv(counter_path)
        except EmptyDataError:
            counter_df = pd.DataFrame(columns=["hero_a", "hero_b", "counter_score"])
        for _, row in counter_df.iterrows():
            counter_map[(str(row["hero_a"]), str(row["hero_b"]))] = float(row["counter_score"])

    scored = []
    for hero in pool:
        hero_key = key_by_name.get(hero, hero)
        base = float(meta_scores.get(hero, meta_scores.get(hero_key, 0.0)))

        ally_synergy = 0.0
        if ally_picks:
            synergy_vals: list[float] = []
            for ally in ally_picks:
                ally_key = key_by_name.get(ally, ally)
                pair = tuple(sorted((hero_key, ally_key)))
                fallback_pair = tuple(sorted((hero, ally)))
                synergy_vals.append(synergy_map.get(pair, synergy_map.get(fallback_pair, 0.5)))
            ally_synergy = sum(synergy_vals) / len(synergy_vals) if synergy_vals else 0.0

        enemy_counter = 0.0
        if enemy_picks:
            counter_vals: list[float] = []
            for enemy in enemy_picks:
                enemy_key = key_by_name.get(enemy, enemy)
                counter_vals.append(counter_map.get((hero_key, enemy_key), counter_map.get((hero, enemy), 0.0)))
            enemy_counter = sum(counter_vals) / len(counter_vals) if counter_vals else 0.0

        score = base * 0.6 + ally_synergy * 0.25 + enemy_counter * 0.15
        scored.append({"hero": hero, "score": round(score, 6)})

    result = pd.DataFrame(scored, columns=["hero", "score"])
    if not result.empty:
        result = result.sort_values("score", ascending=False)
        if top_n is not None:
            result = result.head(top_n)
    result.to_csv(ANALYSIS_DIR / "draft_recommendations.csv", index=False)
    return result


def generate_default_recommendations() -> pd.DataFrame:
    return recommend_picks([], [], top_n=None)
