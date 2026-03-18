from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

from utils import ANALYSIS_DIR, EXPORTS_DIR, PROCESSED_DIR


class DatasetExporter:
    def __init__(self) -> None:
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _read_csv(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
        if path.exists():
            try:
                return pd.read_csv(path)
            except EmptyDataError:
                return pd.DataFrame(columns=columns or [])
        return pd.DataFrame(columns=columns or [])

    @staticmethod
    def _read_json_table(path: Path) -> pd.DataFrame:
        if not path.exists():
            return pd.DataFrame()
        return pd.read_json(path)

    def export_excel(self) -> Path:
        output_path = EXPORTS_DIR / "deadlock_dataset.xlsx"

        heroes = self._read_json_table(PROCESSED_DIR / "heroes.json")
        abilities = self._read_json_table(PROCESSED_DIR / "abilities.json")
        items = self._read_json_table(PROCESSED_DIR / "items.json")
        matches = self._read_json_table(PROCESSED_DIR / "matches.json")

        synergy = self._read_csv(ANALYSIS_DIR / "synergy_matrix.csv")
        counters = self._read_csv(ANALYSIS_DIR / "counter_matrix.csv")
        hero_vs_hero = self._read_csv(ANALYSIS_DIR / "hero_vs_hero_matrix.csv")
        meta = self._read_csv(PROCESSED_DIR.parent / "meta" / "hero_meta_scores.csv")

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            heroes.to_excel(writer, sheet_name="Heroes", index=False)
            abilities.to_excel(writer, sheet_name="Abilities", index=False)
            items.to_excel(writer, sheet_name="Items", index=False)
            matches.to_excel(writer, sheet_name="Matches", index=False)
            synergy.to_excel(writer, sheet_name="Synergy", index=False)
            counters.to_excel(writer, sheet_name="Counters", index=False)
            hero_vs_hero.to_excel(writer, sheet_name="HeroVsHero", index=False)
            meta.to_excel(writer, sheet_name="Meta", index=False)

        return output_path
