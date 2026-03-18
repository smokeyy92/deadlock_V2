from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
META_DIR = DATA_DIR / "meta"
ANALYSIS_DIR = DATA_DIR / "analysis"
EXPORTS_DIR = DATA_DIR / "exports"
SNAPSHOT_DIR = ROOT_DIR / "snapshot"
CONFIG_DIR = ROOT_DIR / "config"


def ensure_directories() -> None:
    for directory in [
        RAW_DIR,
        PROCESSED_DIR,
        META_DIR,
        ANALYSIS_DIR,
        EXPORTS_DIR,
        SNAPSHOT_DIR,
        CONFIG_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
