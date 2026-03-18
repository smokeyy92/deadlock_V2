from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from utils import ANALYSIS_DIR, META_DIR, PROCESSED_DIR, SNAPSHOT_DIR, load_json, save_json


class SnapshotManager:
    def __init__(self) -> None:
        self.snapshot_path = SNAPSHOT_DIR / "state.json"

    def _count(self, name: str) -> int:
        payload = load_json(PROCESSED_DIR / f"{name}.json", default=[])
        return len(payload) if isinstance(payload, list) else 0

    def _latest_patch(self) -> str:
        raw_patches = load_json(PROCESSED_DIR.parent / "raw" / "patches.json", default=[])
        if isinstance(raw_patches, dict):
            raw_patches = raw_patches.get("data") or raw_patches.get("patches") or []
        if not raw_patches:
            return ""
        latest = raw_patches[0]
        if isinstance(latest, dict):
            return str(latest.get("name") or latest.get("version") or "")
        return str(latest)

    def update(self) -> dict[str, Any]:
        state = load_json(self.snapshot_path, default={})
        now = datetime.now(timezone.utc).isoformat()

        state.update(
            {
                "version": state.get("version", "4.0"),
                "hero_count": self._count("heroes"),
                "ability_count": self._count("abilities"),
                "item_count": self._count("items"),
                "match_count": self._count("matches"),
                "dataset_last_generated": now,
                "last_patch_detected": self._latest_patch(),
                "dataset_files": [
                    "deadlock_dataset.xlsx",
                    "hero_vs_hero_matrix.csv",
                    "matchup_predictions.csv",
                ],
                "analysis_files": [
                    "hero_meta_scores.csv",
                    "team_scores.csv",
                    "synergy_matrix.csv",
                    "counter_matrix.csv",
                ],
                "project_modules": [
                    "api_client",
                    "dataset_builder",
                    "synergy_engine",
                    "counter_engine",
                    "meta_analyzer",
                    "draft_engine",
                    "match_predictor",
                ],
                "generated_at": now,
            }
        )

        save_json(self.snapshot_path, state)
        return state
