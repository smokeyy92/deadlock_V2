# 05. Outputs, Snapshot, and Troubleshooting

## Output Artifacts
### Processed datasets
- `data/processed/heroes.json`
- `data/processed/abilities.json`
- `data/processed/items.json`
- `data/processed/matches.json`

### Analysis datasets
- `data/analysis/synergy_matrix.csv`
- `data/analysis/hero_vs_hero_matrix.csv`
- `data/analysis/counter_matrix.csv`
- `data/analysis/team_compositions.csv`
- `data/analysis/team_scores.csv`
- `data/analysis/matchup_predictions.csv`
- `data/analysis/draft_recommendations.csv`

### Meta datasets
- `data/meta/hero_pickrates.csv`
- `data/meta/hero_winrates.csv`
- `data/meta/hero_meta_scores.csv`

### Excel export
- `data/exports/deadlock_dataset.xlsx`

## Snapshot State
State file:
- `snapshot/state.json`

Managed by:
- `src/snapshot_manager.py`

Tracks:
- hero/ability/item/match counts
- generation timestamps
- last detected patch info
- expected dataset and analysis files

## Rollback and Safety
Rollback snapshots are created via:
- `scripts/create_rollback_snapshot.ps1`

Launcher integration:
- `scripts/run_toolkit.bat` creates snapshot before running pipeline.

Typical snapshot path:
- `snapshot/rollback/YYYYMMDD-HHMMSS/`

## Operational Commands
- Full pipeline: `python src/main.py all`
- API only: `python src/main.py api`
- Rebuild processed datasets: `python src/main.py dataset`
- Recompute analytics: `python src/main.py synergy`, `predict`, `counters`, `meta`, `analyze`
- Export: `python src/main.py export`
- GUI: `python src/main.py gui`

## Common Issues and What to Check
1. Very low match count
- Confirm high-tier filters in `src/api_client.py` are expected
- Verify lookback and pull limit constants
- Re-run `python src/main.py api` and check `data/raw/matches.json`

2. Hero IDs showing in GUI
- Ensure `data/processed/heroes.json` is populated
- Re-run `python src/main.py dataset`

3. Empty recommendation tables
- Ensure `analyze` and prerequisite stages were run
- Check `data/analysis/draft_recommendations.csv`

4. Prediction not showing in Team Analysis
- Prediction appears only when draft is complete (6 picks each)
- Verify `data/processed/matches.json` and `data/analysis/hero_vs_hero_matrix.csv` exist

5. Pipeline command failures
- Read terminal output from failing step
- Run single stages to isolate failure
- Check API reachability and response shape

## Team Demo Script (Suggested)
1. Show pipeline controls and run `api` then `dataset`
2. Open generated CSV files and explain score columns
3. Show `deadlock_dataset.xlsx` and sheet structure
4. In GUI, complete draft and show live win% prediction source and sample size
5. Show `snapshot/state.json` and rollback folder to demonstrate operational safety
