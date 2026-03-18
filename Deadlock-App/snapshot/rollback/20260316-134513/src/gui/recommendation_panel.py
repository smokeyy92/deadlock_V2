from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError
from PySide6.QtWidgets import (
    QGroupBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

_BASE = Path(__file__).resolve().parent.parent.parent
_ANALYSIS = _BASE / "data" / "analysis"
_META = _BASE / "data" / "meta"
_PROCESSED_HEROES = _BASE / "data" / "processed" / "heroes.json"


def _safe_read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except EmptyDataError:
        return pd.DataFrame()


class RecommendationPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Recommendations", parent)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>Top Pick Recommendations</b>"))
        self._pick_table = QTableWidget(0, 5)
        self._pick_table.setHorizontalHeaderLabels(["Hero", "Synergy", "Counter", "Role", "Score"])
        self._pick_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._pick_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._pick_table)

        layout.addWidget(QLabel("<b>Top Ban Targets</b>"))
        self._ban_table = QTableWidget(0, 4)
        self._ban_table.setHorizontalHeaderLabels(["Hero", "Meta", "Counter Potential", "Ban Score"])
        self._ban_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._ban_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._ban_table)

    def refresh(
        self,
        ally_picks: list[str] | None = None,
        enemy_picks: list[str] | None = None,
    ) -> None:
        self._populate_picks()
        self._populate_bans()

    def _load_hero_name_map(self) -> dict[str, str]:
        if not _PROCESSED_HEROES.exists():
            return {}
        try:
            data = json.loads(_PROCESSED_HEROES.read_text(encoding="utf-8"))
        except Exception:
            return {}

        name_map: dict[str, str] = {}
        for row in data:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            hid = str(row.get("id") or "").strip()
            hero_id = str(row.get("hero_id") or "").strip()
            slug = str(row.get("slug") or "").strip()

            name_map[name] = name
            if hid:
                name_map[hid] = name
            if hero_id:
                name_map[hero_id] = name
            if slug:
                name_map[slug] = name
        return name_map

    def _load_hero_info(self) -> dict[str, dict[str, str]]:
        if not _PROCESSED_HEROES.exists():
            return {}
        try:
            data = json.loads(_PROCESSED_HEROES.read_text(encoding="utf-8"))
        except Exception:
            return {}

        info: dict[str, dict[str, str]] = {}
        for row in data:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            role = str(row.get("role") or "unknown")
            id_key = str(row.get("id") or "").strip()
            hero_id_key = str(row.get("hero_id") or "").strip()
            slug_key = str(row.get("slug") or "").strip()

            entry = {
                "name": name,
                "role": role,
                "id": id_key,
                "hero_id": hero_id_key,
                "slug": slug_key,
            }

            info[name] = entry
            if id_key:
                info[id_key] = entry
            if hero_id_key:
                info[hero_id_key] = entry
            if slug_key:
                info[slug_key] = entry
        return info

    @staticmethod
    def _resolve_metric(metric_map: dict[str, float], hero: str, hero_info: dict[str, dict[str, str]]) -> float:
        if hero in metric_map:
            return float(metric_map[hero])

        entry = hero_info.get(hero, {})
        for key in [entry.get("id"), entry.get("hero_id"), entry.get("slug"), entry.get("name")]:
            if key and key in metric_map:
                return float(metric_map[key])
        return 0.0

    @staticmethod
    def _display_hero(hero_key: str, hero_name_map: dict[str, str]) -> str:
        mapped = hero_name_map.get(hero_key)
        if mapped and mapped != hero_key:
            return f"{mapped} ({hero_key})"
        return mapped or hero_key

    # ── private helpers ──────────────────────────────────────────────────────

    def _populate_picks(self) -> None:
        recs = _safe_read(_ANALYSIS / "draft_recommendations.csv")
        synergy_df = _safe_read(_ANALYSIS / "synergy_matrix.csv")
        counter_df = _safe_read(_ANALYSIS / "counter_matrix.csv")
        hero_name_map = self._load_hero_name_map()
        hero_info = self._load_hero_info()

        synergy_map: dict[str, float] = {}
        if not synergy_df.empty and "hero_a" in synergy_df.columns:
            grouped = synergy_df.groupby("hero_a")["synergy_score"].mean().to_dict()
            synergy_map = {str(k): float(v) for k, v in grouped.items()}

        counter_map: dict[str, float] = {}
        if not counter_df.empty and "hero_a" in counter_df.columns:
            grouped = counter_df.groupby("hero_a")["counter_score"].mean().to_dict()
            counter_map = {str(k): float(v) for k, v in grouped.items()}

        self._pick_table.setRowCount(0)
        if recs.empty or "hero" not in recs.columns:
            return

        recs = recs.sort_values("score", ascending=False)
        for _, rec in recs.iterrows():
            hero = str(rec.get("hero", ""))
            score = round(float(rec.get("score", 0.0)), 3)
            syn = round(self._resolve_metric(synergy_map, hero, hero_info), 3)
            ctr = round(self._resolve_metric(counter_map, hero, hero_info), 3)
            role = hero_info.get(hero, {}).get("role") or "unknown"
            row = self._pick_table.rowCount()
            self._pick_table.insertRow(row)
            self._pick_table.setItem(row, 0, QTableWidgetItem(self._display_hero(hero, hero_name_map)))
            self._pick_table.setItem(row, 1, QTableWidgetItem(str(syn)))
            self._pick_table.setItem(row, 2, QTableWidgetItem(str(ctr)))
            self._pick_table.setItem(row, 3, QTableWidgetItem(role.title()))
            self._pick_table.setItem(row, 4, QTableWidgetItem(str(score)))

    def _populate_bans(self) -> None:
        meta = _safe_read(_META / "hero_meta_scores.csv")
        hero_name_map = self._load_hero_name_map()
        self._ban_table.setRowCount(0)
        if meta.empty or "meta_score" not in meta.columns:
            return

        for _, ban in meta.sort_values("meta_score", ascending=False).head(5).iterrows():
            hero = str(ban.get("hero", ""))
            meta_score = round(float(ban.get("meta_score", 0.0)), 3)
            ctr = round(float(ban.get("counter_score", 0.0)) if "counter_score" in ban else 0.0, 3)
            ban_score = round(meta_score * 0.7 + ctr * 0.3, 3)
            row = self._ban_table.rowCount()
            self._ban_table.insertRow(row)
            self._ban_table.setItem(row, 0, QTableWidgetItem(self._display_hero(hero, hero_name_map)))
            self._ban_table.setItem(row, 1, QTableWidgetItem(str(meta_score)))
            self._ban_table.setItem(row, 2, QTableWidgetItem(str(ctr)))
            self._ban_table.setItem(row, 3, QTableWidgetItem(str(ban_score)))
