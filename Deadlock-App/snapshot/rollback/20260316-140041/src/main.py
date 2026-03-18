from __future__ import annotations

import argparse
import time
from typing import Callable

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from api_client import DeadlockAPIClient
from counter_engine import compute_counter_matrix
from dataset_builder import DatasetBuilder
from draft_engine import generate_default_recommendations
from exporter import DatasetExporter
from match_predictor import compute_hero_vs_hero_matrix, compute_team_compositions, predict_matchups
from meta_analyzer import compute_meta_scores
from snapshot_manager import SnapshotManager
from synergy_engine import compute_synergy_matrix
from team_analyzer import analyze_teams
from utils import ensure_directories

console = Console()


def _run_step(step_name: str, step_func: Callable[[], None], index: int, total: int) -> None:
    console.print(f"[cyan][{index}/{total}] Starting: {step_name}[/cyan]")
    start = time.perf_counter()
    try:
        step_func()
    except Exception as exc:
        elapsed = time.perf_counter() - start
        console.print(f"[bold red][{index}/{total}] FAILED: {step_name} after {elapsed:.2f}s[/bold red]")
        console.print(f"[red]Error: {type(exc).__name__}: {exc}[/red]")
        raise
    elapsed = time.perf_counter() - start
    console.print(f"[green][{index}/{total}] Done: {step_name} ({elapsed:.2f}s)[/green]")


def run_api() -> None:
    client = DeadlockAPIClient()
    client.fetch_all()
    console.print("[green]API ingestion complete.[/green]")


def run_dataset() -> None:
    builder = DatasetBuilder()
    builder.build_all()


def run_synergy() -> None:
    compute_synergy_matrix()
    console.print("[green]Synergy matrix generated.[/green]")


def run_counters() -> None:
    compute_counter_matrix()
    console.print("[green]Counter matrix generated.[/green]")


def run_meta() -> None:
    compute_meta_scores()
    console.print("[green]Meta files generated.[/green]")


def run_predict() -> None:
    compute_hero_vs_hero_matrix()
    compute_team_compositions()
    predict_matchups()
    console.print("[green]Predictive files generated.[/green]")


def run_analyze() -> None:
    analyze_teams()
    generate_default_recommendations()
    console.print("[green]Team and draft analysis generated.[/green]")


def run_export() -> None:
    output = DatasetExporter().export_excel()
    console.print(f"[green]Exported {output}[/green]")


def run_snapshot() -> None:
    state = SnapshotManager().update()
    console.print(f"[green]Snapshot updated with match_count={state.get('match_count', 0)}[/green]")


def run_gui() -> None:
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        import sys as _sys
        app = QApplication.instance() or QApplication(_sys.argv)
        window = MainWindow()
        window.show()
        app.exec()
    except ImportError as exc:
        console.print(f"[red]GUI requires PySide6: pip install PySide6[/red]")
        raise


def run_all() -> None:
    steps: list[tuple[str, Callable[[], None]]] = [
        ("API ingestion", run_api),
        ("Dataset build", run_dataset),
        ("Synergy matrix", run_synergy),
        ("Predictive matrices", run_predict),
        ("Counter matrix", run_counters),
        ("Meta analysis", run_meta),
        ("Team and draft analysis", run_analyze),
        ("Excel export", run_export),
        ("Snapshot update", run_snapshot),
    ]

    total_steps = len(steps)
    snapshot_completed = False
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Pipeline progress", total=total_steps)
        try:
            for idx, (name, func) in enumerate(steps, start=1):
                progress.update(task, description=f"Running step {idx}/{total_steps}: {name}")
                _run_step(name, func, idx, total_steps)
                if name == "Snapshot update":
                    snapshot_completed = True
                progress.advance(task)
        except Exception:
            if not snapshot_completed:
                console.print("[yellow]Attempting guardrail snapshot after failure...[/yellow]")
                try:
                    run_snapshot()
                except Exception as snapshot_exc:
                    console.print(f"[red]Guardrail snapshot failed: {snapshot_exc}[/red]")
            raise

    console.print("[bold green]Pipeline complete.[/bold green]")


def main() -> None:
    ensure_directories()

    parser = argparse.ArgumentParser(description="Deadlock Competitive Intelligence Toolkit")
    parser.add_argument(
        "command",
        choices=["api", "dataset", "synergy", "counters", "meta", "predict", "analyze", "export", "snapshot", "gui", "all"],
        help="Pipeline command",
    )
    args = parser.parse_args()

    commands: dict[str, Callable[[], None]] = {
        "api": run_api,
        "dataset": run_dataset,
        "synergy": run_synergy,
        "counters": run_counters,
        "meta": run_meta,
        "predict": run_predict,
        "analyze": run_analyze,
        "export": run_export,
        "snapshot": run_snapshot,
        "gui": run_gui,
        "all": run_all,
    }

    selected = args.command
    if selected == "all":
        commands[selected]()
    else:
        _run_step(selected, commands[selected], 1, 1)
        if selected not in {"snapshot", "gui"}:
            _run_step("snapshot", run_snapshot, 2, 2)


if __name__ == "__main__":
    main()
