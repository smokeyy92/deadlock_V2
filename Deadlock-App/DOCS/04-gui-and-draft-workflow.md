# 04. GUI and Draft Workflow

## Entry Point
- `python src/main.py gui`

Main window implementation:
- `src/gui/main_window.py`

## Main Panels
1. Pipeline Controls
2. Draft Timeline
3. Recommendations
4. Team Analysis
5. Dataset Status

## Draft Timeline Logic
Implementation:
- `src/gui/draft_timeline_panel.py`

A fixed turn order enforces legal pick/ban sequence.
- Prevents duplicate heroes
- Validates team and action against current step
- Supports:
  - Confirm Action
  - Undo Last Step
  - Reset Draft
  - Auto Best Pick

## Recommendations Panel
Implementation:
- `src/gui/recommendation_panel.py`

Displays:
- Top Pick Recommendations
- Top Ban Targets

Current behavior:
- Ban list is full ranked list (not only top 5)
- Hero display resolves IDs to readable names when mappings exist

## Team Analysis Panel
Implementation:
- `src/gui/team_analysis_panel.py`

Shows for each team:
- Role bars (Tank, Carry, Support, Initiator, Assassin, **Flex**)
- Team strength score
- Role-to-hero lists (which hero is assigned to each role bucket)

Role assignments are read from `config/hero_metadata.json` at refresh time. Heroes whose role is unrecognised or absent fall back to the **Flex** bucket so they are always visible in the graph — no hero is silently dropped from the count.

## Draft-Complete Win Prediction
Implementation:
- `src/gui/main_window.py`

When draft reaches full completion (6 picks each):
1. Try exact composition lookup in `data/processed/matches.json`
2. If no exact sample exists, fallback to weighted hero-vs-hero matrix from `data/analysis/hero_vs_hero_matrix.csv`

Displayed in Team Analysis as:
- Team A win chance percentage
- Source (`exact composition` or `hero matchups`)
- Effective sample size (`n=`)

## Relaunch UX
Relaunch button is under Pipeline Controls.
- Triggered from `src/gui/pipeline_panel.py`
- Relaunch handled by `src/gui/main_window.py`
