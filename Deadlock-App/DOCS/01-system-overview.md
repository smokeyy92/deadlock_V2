# 01. System Overview

## What the Application Does
The application is a local competitive intelligence toolkit for Deadlock. It performs a full data pipeline and then powers a draft assistant GUI.

Main capabilities:
1. Pull raw game data from API endpoints
2. Build normalized hero, ability, item, and match datasets
3. Compute analytics (synergy, counters, team composition, meta scores)
4. Generate draft recommendations and matchup predictions
5. Export an Excel workbook for analyst consumption
6. Provide an interactive draft GUI with live recommendations and team analysis

## End-to-End Pipeline
Primary orchestrator: `src/main.py`

Pipeline stages (`python src/main.py all`):
1. API ingestion
2. Dataset build
3. Synergy matrix
4. Predictive matrices
5. Counter matrix
6. Meta analysis
7. Team and draft analysis
8. Excel export
9. Snapshot update

## Core Module Responsibilities
- `src/api_client.py`: API fetch + raw JSON persistence
- `src/dataset_builder.py`: raw -> processed datasets
- `src/synergy_engine.py`: pair synergy win rates
- `src/match_predictor.py`: hero-vs-hero matrix, team compositions, per-match probabilities
- `src/counter_engine.py`: counter score matrix from hero-vs-hero
- `src/meta_analyzer.py`: pick rate, win rate, and composite meta score
- `src/draft_engine.py`: recommendation scoring for draft candidates
- `src/team_analyzer.py`: role-composition team strength score
- `src/exporter.py`: Excel output
- `src/gui/*`: production draft UI panels
- `src/snapshot_manager.py`: state tracking in `snapshot/state.json`

## Competitive Scope (Current)
Current ingestion is intentionally focused on high-skill competitive relevance:
- Rank floor: `MIN_BADGE_LEVEL = 114` (Eternus 4+)
- Time window: `MATCH_LOOKBACK_DAYS = 14`
- Match pull ceiling: `MATCH_PULL_LIMIT = 10000`

This means model outputs are based on recent high-tier match behavior rather than broad all-rank data.
