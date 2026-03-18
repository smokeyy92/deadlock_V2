from __future__ import annotations

from typing import Any

import requests
from rich.console import Console

from utils import RAW_DIR, save_json


# Badge encoding: first digits = rank tier, last digit = subtier.
# Eternus 4 → tier 11, subtier 4 → badge value 114.
# All match and analytics pulls are filtered to Eternus 4+ games only.
MIN_BADGE_LEVEL: int = 114


class DeadlockAPIClient:
    def __init__(self, base_url: str = "https://api.deadlock-api.com", timeout: int = 25) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.console = Console()

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        cleaned = endpoint.lstrip("/")
        if cleaned.startswith("v1/"):
            candidates = [f"{self.base_url}/{cleaned}"]
        else:
            candidates = [
                f"{self.base_url}/v1/{cleaned}",
                f"{self.base_url}/{cleaned}",
            ]

        last_error: requests.RequestException | None = None
        for url in candidates:
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:
                last_error = exc

        self.console.print(f"[yellow]API request failed for {endpoint}: {last_error}[/yellow]")
        return []

    def _sql(self, query: str) -> list[dict[str, Any]]:
        payload = self._get("/v1/sql", params={"query": query})
        return payload if isinstance(payload, list) else []

    def _save_raw(self, name: str, payload: Any) -> None:
        path = RAW_DIR / f"{name}.json"
        save_json(path, payload)

    def get_heroes(self) -> Any:
        data = self._sql("SELECT id, name FROM heroes ORDER BY id")
        self._save_raw("heroes", data)
        return data

    def get_abilities(self) -> Any:
        heroes = self.get_heroes()
        abilities: list[dict[str, Any]] = []
        seen: set[tuple[int, int]] = set()

        for hero in heroes:
            hero_id = int(hero.get("id", 0) or 0)
            if hero_id <= 0:
                continue

            payload = self._get(
                "/v1/analytics/ability-order-stats",
                params={"hero_id": hero_id, "min_matches": 1, "min_average_badge": MIN_BADGE_LEVEL},
            )
            if not isinstance(payload, list):
                continue

            for entry in payload:
                if not isinstance(entry, dict):
                    continue
                for ability_id in entry.get("abilities", []):
                    if not isinstance(ability_id, int):
                        continue
                    key = (hero_id, ability_id)
                    if key in seen:
                        continue
                    seen.add(key)
                    abilities.append(
                        {
                            "id": ability_id,
                            "hero_id": hero_id,
                            "name": f"Ability {ability_id}",
                            "cooldown": None,
                            "damage": None,
                            "description": "",
                            "scaling": {},
                        }
                    )

        data = sorted(abilities, key=lambda x: (x["hero_id"], x["id"]))
        self._save_raw("abilities", data)
        return data

    def get_items(self) -> Any:
        data = self._sql("SELECT id, name, cost, tier, type, slot_type FROM items ORDER BY id")
        self._save_raw("items", data)
        return data

    def get_players(self) -> Any:
        data = self._get("/v1/leaderboard/NAmerica")
        self._save_raw("players", data)
        return data

    def get_patches(self) -> Any:
        data = self._get("/v1/patches")
        self._save_raw("patches", data)
        return data

    def get_hero_stats(self) -> Any:
        data = self._get("/v1/analytics/hero-stats", params={"min_average_badge": MIN_BADGE_LEVEL})
        self._save_raw("hero_stats", data)
        return data

    def get_item_stats(self) -> Any:
        data = self._get("/v1/analytics/item-stats", params={"min_matches": 1, "min_average_badge": MIN_BADGE_LEVEL})
        self._save_raw("item_stats", data)
        return data

    def get_leaderboards(self) -> Any:
        data = self._get("/v1/builds", params={"limit": 100})
        self._save_raw("leaderboards", data)
        return data

    def get_matches(self, limit: int = 500) -> list[dict[str, Any]]:
        recent = self._get("/v1/matches/recently-fetched")
        if not isinstance(recent, list):
            recent = []

        matches: list[dict[str, Any]] = []
        for row in recent[:limit]:
            if not isinstance(row, dict) or "match_id" not in row:
                continue

            # Skip matches that are not Eternus 4+ on both teams.
            badge0 = row.get("average_badge_team0")
            badge1 = row.get("average_badge_team1")
            if badge0 is None or badge1 is None or badge0 < MIN_BADGE_LEVEL or badge1 < MIN_BADGE_LEVEL:
                continue
            match_id = str(row.get("match_id"))
            metadata = self.get_match_details(match_id)
            match_info = metadata.get("match_info", {}) if isinstance(metadata, dict) else {}
            players = match_info.get("players", []) if isinstance(match_info, dict) else []

            team_a_heroes: list[str] = []
            team_b_heroes: list[str] = []
            hero_kills: dict[str, int] = {}
            hero_deaths: dict[str, int] = {}
            hero_assists: dict[str, int] = {}

            ranks: list[float] = []
            for player in players:
                if not isinstance(player, dict):
                    continue
                hero_id = str(player.get("hero_id", ""))
                team = int(player.get("team", -1) or -1)
                if hero_id:
                    if team == 0:
                        team_a_heroes.append(hero_id)
                    elif team == 1:
                        team_b_heroes.append(hero_id)
                    hero_kills[hero_id] = int(player.get("kills", 0) or 0)
                    hero_deaths[hero_id] = int(player.get("deaths", 0) or 0)
                    hero_assists[hero_id] = int(player.get("assists", 0) or 0)

                badge = player.get("ranked_rank")
                if isinstance(badge, (int, float)):
                    ranks.append(float(badge))

            winning_team = int(match_info.get("winning_team", -1) or -1) if isinstance(match_info, dict) else -1
            winner = "team_a" if winning_team == 0 else "team_b" if winning_team == 1 else ""

            matches.append(
                {
                    "match_id": match_id,
                    "patch": str(match_info.get("cluster", "unknown")) if isinstance(match_info, dict) else "unknown",
                    "timestamp": str(row.get("start_time", "")),
                    "duration": int(match_info.get("duration_s", row.get("duration_s", 0)) or 0),
                    "team_a_heroes": team_a_heroes,
                    "team_b_heroes": team_b_heroes,
                    "winner": winner,
                    "player_ranks": ranks,
                    "hero_damage": {},
                    "hero_kills": hero_kills,
                    "hero_deaths": hero_deaths,
                    "hero_assists": hero_assists,
                }
            )

        self._save_raw("matches", matches)
        return matches

    def get_match_details(self, match_id: str) -> Any:
        return self._get(f"/v1/matches/{match_id}/metadata")

    def fetch_all(self) -> dict[str, Any]:
        return {
            "heroes": self.get_heroes(),
            "abilities": self.get_abilities(),
            "items": self.get_items(),
            "matches": self.get_matches(),
            "players": self.get_players(),
            "patches": self.get_patches(),
            "hero_stats": self.get_hero_stats(),
            "item_stats": self.get_item_stats(),
            "leaderboards": self.get_leaderboards(),
        }
