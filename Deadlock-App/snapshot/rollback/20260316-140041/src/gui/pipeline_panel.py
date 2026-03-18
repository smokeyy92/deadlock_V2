from __future__ import annotations

import sys
import subprocess
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_MAIN_PY = Path(__file__).resolve().parent.parent / "main.py"
_CWD = _MAIN_PY.parent.parent


class _Worker(QObject):
    finished = Signal(bool, str)

    def __init__(self, command: str) -> None:
        super().__init__()
        self.command = command

    def run(self) -> None:
        try:
            result = subprocess.run(
                [sys.executable, str(_MAIN_PY), self.command],
                capture_output=True,
                text=True,
                cwd=str(_CWD),
            )
            output = (result.stdout + result.stderr).strip()
            self.finished.emit(result.returncode == 0, output[-1200:])
        except Exception as exc:
            self.finished.emit(False, str(exc))


class PipelinePanel(QGroupBox):
    pipeline_done = Signal()

    _BUTTONS: list[tuple[str, str]] = [
        ("Extract Hero Data", "api"),
        ("Build Datasets", "dataset"),
        ("Compute Synergy Matrix", "synergy"),
        ("Compute Counter Matrix", "counters"),
        ("Run Meta Analysis", "meta"),
        ("Predict Matchups", "predict"),
        ("Analyze Teams & Draft", "analyze"),
        ("Export Excel Dataset", "export"),
        ("Update Snapshot", "snapshot"),
        ("▶  Run Full Pipeline", "all"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Pipeline Controls", parent)
        layout = QVBoxLayout(self)

        self._btns: dict[str, QPushButton] = {}
        for label, cmd in self._BUTTONS:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _checked, c=cmd: self._launch(c))
            layout.addWidget(btn)
            self._btns[cmd] = btn

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status = QLabel("Ready")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)
        layout.addStretch()

        self._thread: QThread | None = None
        self._worker: _Worker | None = None

    def _launch(self, command: str) -> None:
        self._set_busy(True, f"Running: {command}…")
        self._thread = QThread()
        self._worker = _Worker(command)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_done)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_done(self, success: bool, output: str) -> None:
        if success:
            self._status.setText("✔ Done")
        else:
            last = output.splitlines()
            snippet = "\n".join(last[-6:]) if last else output
            self._status.setText(f"✘ Error:\n{snippet}")
        self._set_busy(False)
        self.pipeline_done.emit()

    def _set_busy(self, busy: bool, msg: str = "Ready") -> None:
        self._progress.setVisible(busy)
        self._status.setText(msg)
        for btn in self._btns.values():
            btn.setEnabled(not busy)
