from __future__ import annotations

import pandas as pd

from utils import ANALYSIS_DIR


def compute_counter_matrix() -> pd.DataFrame:
    hero_vs_hero_path = ANALYSIS_DIR / "hero_vs_hero_matrix.csv"
    if not hero_vs_hero_path.exists():
        df = pd.DataFrame(columns=["hero_a", "hero_b", "counter_score"])
        df.to_csv(ANALYSIS_DIR / "counter_matrix.csv", index=False)
        return df

    hero_vs_hero = pd.read_csv(hero_vs_hero_path)
    if hero_vs_hero.empty:
        df = pd.DataFrame(columns=["hero_a", "hero_b", "counter_score"])
        df.to_csv(ANALYSIS_DIR / "counter_matrix.csv", index=False)
        return df

    matrix = hero_vs_hero.copy()
    matrix["counter_score"] = matrix["winrate"].fillna(0.5) - 0.5
    df = matrix[["hero_a", "hero_b", "counter_score"]].sort_values(["hero_a", "hero_b"])
    df.to_csv(ANALYSIS_DIR / "counter_matrix.csv", index=False)
    return df
