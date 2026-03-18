from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

_ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "heroes"


def load_hero_pixmap(hero_name: str, size: int = 32) -> QPixmap:
    slug = (
        hero_name.lower()
        .replace("&", "and")
        .replace("'", "")
        .replace("-", "_")
        .replace(" ", "_")
    )
    path = _ASSETS_DIR / f"{slug}.png"
    if path.exists():
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            return pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    placeholder = QPixmap(size, size)
    placeholder.fill(Qt.GlobalColor.darkGray)
    return placeholder
