from __future__ import annotations

import re
from typing import Any

from rich.console import Console

from utils import CONFIG_DIR, PROCESSED_DIR, RAW_DIR, as_list, load_json, safe_div, save_json

_ROLE_BUCKETS = ["hypercarry", "offcarry", "frontliner", "support", "spirit", "initiator"]

# Maps internal role name -> human-readable bucket label used in roles.json
_ROLE_BUCKET_LABELS: dict[str, str] = {
    "hypercarry": "Hypercarry",
    "offcarry": "Offcarry",
    "frontliner": "Frontliner/Tank",
    "support": "Support",
    "spirit": "Spirit/Flex/Hybrid",
    "initiator": "Pick/Initiator/Catch",
}


def sync_roles_from_metadata() -> dict[str, list[str]]:
    """Regenerate config/roles.json from config/hero_metadata.json.

    Every hero in hero_metadata.json is placed in exactly one role bucket.
    Roles not in _ROLE_BUCKETS are mapped to 'initiator'.  Returns the generated
    mapping and writes it to config/roles.json.
    """
    metadata: dict = load_json(CONFIG_DIR / "hero_metadata.json", default={})
    roles: dict[str, list[str]] = {label: [] for label in _ROLE_BUCKET_LABELS.values()}
    for slug, info in metadata.items():
        role = str(info.get("role") or "initiator").lower()
        label = _ROLE_BUCKET_LABELS.get(role, "Pick/Initiator/Catch")
        roles[label].append(slug)
    for bucket in roles:
        roles[bucket].sort()
    save_json(CONFIG_DIR / "roles.json", roles)
    return roles


class DatasetBuilder:
    def __init__(self) -> None:
        self.console = Console()

    def _load_raw(self, name: str) -> Any:
        return load_json(RAW_DIR / f"{name}.json", default=[])

    @staticmethod
    def _to_slug(name: str) -> str:
        s = name.lower()
        s = s.replace("&", "and")
        s = re.sub(r"['\-]", "", s)
        s = re.sub(r"\s+", "_", s.strip())
        return s

    def build_heroes(self) -> list[dict[str, Any]]:
        raw_heroes = self._load_raw("heroes")
        if isinstance(raw_heroes, dict):
            raw_heroes = raw_heroes.get("data") or raw_heroes.get("heroes") or []

        # Load config/hero_metadata.json for role/tags/abilities
        metadata: dict[str, Any] = load_json(CONFIG_DIR / "hero_metadata.json", default={})

        # Load hero_stats and build hero_id -> stats lookup
        raw_stats = self._load_raw("hero_stats")
        if isinstance(raw_stats, dict):
            raw_stats = raw_stats.get("data") or raw_stats.get("heroes") or []
        total_matches_all = 0
        for stat in as_list(raw_stats):
            if not isinstance(stat, dict):
                continue
            total_matches_all += int(stat.get("matches", 0) or 0)

        stats_by_id: dict[str, dict[str, Any]] = {}
        for stat in as_list(raw_stats):
            if not isinstance(stat, dict):
                continue
            hid = str(stat.get("hero_id") or stat.get("id") or "")
            if not hid:
                continue
            wins = int(stat.get("wins", 0) or 0)
            losses = int(stat.get("losses", 0) or 0)
            matches = int(stat.get("matches", wins + losses) or wins + losses)
            total_kills = float(stat.get("total_kills", 0.0) or 0.0)
            total_deaths = float(stat.get("total_deaths", 0.0) or 0.0)
            total_assists = float(stat.get("total_assists", 0.0) or 0.0)
            pickrate_from_matches = safe_div(matches, total_matches_all)
            stats_by_id[hid] = {
                "winrate": round(safe_div(wins, matches), 6),
                "pickrate": round(
                    float(
                        stat.get("pick_rate")
                        or stat.get("pickrate")
                        or pickrate_from_matches
                    ),
                    6,
                ),
                "avg_kills": round(
                    float(stat.get("avg_kills") or safe_div(total_kills, matches)),
                    3,
                ),
                "avg_deaths": round(
                    float(stat.get("avg_deaths") or safe_div(total_deaths, matches)),
                    3,
                ),
                "avg_assists": round(
                    float(stat.get("avg_assists") or safe_div(total_assists, matches)),
                    3,
                ),
                "games": matches,
            }

        raw_abilities = self._load_raw("abilities")
        if isinstance(raw_abilities, dict):
            raw_abilities = raw_abilities.get("data") or raw_abilities.get("abilities") or []
        abilities_by_hero: dict[str, list[str]] = {}
        for ability in as_list(raw_abilities):
            if not isinstance(ability, dict):
                continue
            hid = str(ability.get("hero_id") or ability.get("hero") or "")
            if not hid:
                continue
            ability_name = str(ability.get("name") or ability.get("ability_name") or ability.get("id") or "").strip()
            if not ability_name:
                continue
            abilities_by_hero.setdefault(hid, [])
            if ability_name not in abilities_by_hero[hid]:
                abilities_by_hero[hid].append(ability_name)

        heroes: list[dict[str, Any]] = []
        for idx, hero in enumerate(as_list(raw_heroes)):
            if not isinstance(hero, dict):
                continue
            hero_id = str(hero.get("id") or hero.get("hero_id") or idx)
            name = str(hero.get("name") or hero.get("internal_name") or hero_id)
            slug = self._to_slug(name)
            meta = metadata.get(slug, {})
            hero_stats = stats_by_id.get(hero_id, {})
            ability_list = as_list(meta.get("abilities") or hero.get("abilities"))
            if not ability_list:
                ability_list = abilities_by_hero.get(hero_id, [])
            heroes.append(
                {
                    "id": int(hero_id) if str(hero_id).isdigit() else idx,
                    "hero_id": hero_id,
                    "name": name,
                    "slug": slug,
                    "role": meta.get("role") or hero.get("role") or "unknown",
                    "tags": as_list(meta.get("tags") or hero.get("tags")),
                    "stats": {
                        "winrate": hero_stats.get("winrate", 0.0),
                        "pickrate": hero_stats.get("pickrate", 0.0),
                        "avg_kills": hero_stats.get("avg_kills", 0.0),
                        "avg_deaths": hero_stats.get("avg_deaths", 0.0),
                        "avg_assists": hero_stats.get("avg_assists", 0.0),
                        "games": hero_stats.get("games", 0),
                    },
                    "abilities": ability_list,
                }
            )

        heroes.sort(key=lambda x: x["name"].lower())
        save_json(PROCESSED_DIR / "heroes.json", heroes)
        return heroes

    def build_abilities(self) -> list[dict[str, Any]]:
        raw_abilities = self._load_raw("abilities")
        if isinstance(raw_abilities, dict):
            raw_abilities = raw_abilities.get("data") or raw_abilities.get("abilities") or []

        abilities: list[dict[str, Any]] = []
        for idx, ability in enumerate(as_list(raw_abilities)):
            if not isinstance(ability, dict):
                continue
            ability_id = str(ability.get("id") or ability.get("ability_id") or idx)
            abilities.append(
                {
                    "ability_id": ability_id,
                    "hero_id": str(ability.get("hero_id") or ability.get("hero") or ""),
                    "name": str(ability.get("name") or ability_id),
                    "cooldown": ability.get("cooldown", 0),
                    "damage": ability.get("damage", 0),
                    "description": str(ability.get("description") or ""),
                    "scaling": ability.get("scaling", {}),
                }
            )

        abilities.sort(key=lambda x: x["name"].lower())
        save_json(PROCESSED_DIR / "abilities.json", abilities)
        return abilities

    def build_items(self) -> list[dict[str, Any]]:
        raw_items = self._load_raw("items")
        if isinstance(raw_items, dict):
            raw_items = raw_items.get("data") or raw_items.get("items") or []

        items: list[dict[str, Any]] = []
        for idx, item in enumerate(as_list(raw_items)):
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or item.get("item_id") or idx)
            items.append(
                {
                    "item_id": item_id,
                    "name": str(item.get("name") or item_id),
                    "cost": item.get("cost", 0),
                    "stats": item.get("stats", {}),
                    "build_path": as_list(item.get("build_path")),
                }
            )

        items.sort(key=lambda x: x["name"].lower())
        save_json(PROCESSED_DIR / "items.json", items)
        return items

    def build_matches(self) -> list[dict[str, Any]]:
        raw_matches = self._load_raw("matches")
        if isinstance(raw_matches, dict):
            raw_matches = raw_matches.get("data") or raw_matches.get("matches") or []

        matches: list[dict[str, Any]] = []
        for idx, match in enumerate(as_list(raw_matches)):
            if not isinstance(match, dict):
                continue
            team_a = [str(v) for v in as_list(match.get("team_a_heroes") or match.get("team1") or [])]
            team_b = [str(v) for v in as_list(match.get("team_b_heroes") or match.get("team2") or [])]

            matches.append(
                {
                    "match_id": str(match.get("match_id") or match.get("id") or idx),
                    "patch": str(match.get("patch") or "unknown"),
                    "timestamp": str(match.get("timestamp") or ""),
                    "duration": int(match.get("duration") or 0),
                    "team_a_heroes": team_a,
                    "team_b_heroes": team_b,
                    "winner": str(match.get("winner") or ""),
                    "player_ranks": as_list(match.get("player_ranks")),
                    "hero_damage": match.get("hero_damage", {}),
                    "hero_kills": match.get("hero_kills", {}),
                    "hero_deaths": match.get("hero_deaths", {}),
                    "hero_assists": match.get("hero_assists", {}),
                }
            )

        matches.sort(key=lambda x: x["match_id"])
        save_json(PROCESSED_DIR / "matches.json", matches)
        return matches

    def build_all(self) -> dict[str, list[dict[str, Any]]]:
        heroes = self.build_heroes()
        abilities = self.build_abilities()
        items = self.build_items()
        matches = self.build_matches()
        self.console.print(
            f"[green]Processed datasets -> heroes={len(heroes)} abilities={len(abilities)} items={len(items)} matches={len(matches)}[/green]"
        )
        return {
            "heroes": heroes,
            "abilities": abilities,
            "items": items,
            "matches": matches,
        }
