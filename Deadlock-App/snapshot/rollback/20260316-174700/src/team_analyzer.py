from __future__ import annotations

import re
from collections import Counter

import pandas as pd

from utils import ANALYSIS_DIR, CONFIG_DIR, PROCESSED_DIR, load_json

_ROLE_BUCKETS = {"tank", "carry", "support", "initiator", "assassin", "flex"}


def _load_metadata_roles() -> dict[str, str]:
    """Return slug -> role mapping from config/hero_metadata.json."""
    metadata: dict = load_json(CONFIG_DIR / "hero_metadata.json", default={})
    roles: dict[str, str] = {}
    for slug, info in metadata.items():
        role = str(info.get("role") or "flex").lower()
        roles[slug] = role if role in _ROLE_BUCKETS else "flex"
    return roles


def _to_slug(name: str) -> str:
    s = name.lower().replace("&", "and").replace("'", "").replace("-", "")
    return re.sub(r"\s+", "_", s.strip())


def score_team(team: list[str]) -> float:
    if not team:
        return 0.0

    metadata_roles = _load_metadata_roles()
    role_bias = Counter()
    for hero in team:
        slug = _to_slug(str(hero))
        role = metadata_roles.get(slug, "flex")
        role_bias[role] += 1

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
