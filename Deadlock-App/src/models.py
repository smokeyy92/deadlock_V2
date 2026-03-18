from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HeroRecord:
    hero_id: str
    name: str
    role: str = "unknown"
    tags: list[str] = field(default_factory=list)
    difficulty: float = 0.0
    stats: dict[str, Any] = field(default_factory=dict)
    abilities: list[str] = field(default_factory=list)


@dataclass
class MatchRecord:
    match_id: str
    patch: str
    timestamp: str
    duration: int
    team_a_heroes: list[str]
    team_b_heroes: list[str]
    winner: str
    player_ranks: list[float] = field(default_factory=list)
    hero_damage: dict[str, float] = field(default_factory=dict)
    hero_kills: dict[str, int] = field(default_factory=dict)
    hero_deaths: dict[str, int] = field(default_factory=dict)
    hero_assists: dict[str, int] = field(default_factory=dict)
