# 03. Data Processing and Calculations

## Dataset Builder (`src/dataset_builder.py`)
Raw inputs are merged into processed datasets:
- `data/processed/heroes.json`
- `data/processed/abilities.json`
- `data/processed/items.json`
- `data/processed/matches.json`

### Hero dataset merge strategy
Combines:
1. Raw hero list
2. Hero analytics stats
3. `config/hero_metadata.json` for role/tags/abilities fallback

`config/roles.json` is automatically regenerated from `config/hero_metadata.json` every time the dataset build step runs (`python src/main.py dataset` or `all`). It is the **generated** output, not the source of truth. The Deadlock API does not currently expose a hero-role endpoint; all role data originates from `config/hero_metadata.json`.

### Core per-hero stats
For each hero:
- `winrate = wins / matches`
- `pickrate = matches / total_match_sides` (or API-provided value if present)
- `avg_kills = total_kills / matches`
- `avg_deaths = total_deaths / matches`
- `avg_assists = total_assists / matches`

## Synergy (`src/synergy_engine.py`)
For hero pairs on the same team:
- Count pair games and wins
- Compute:
- `synergy_score = pair_wins / pair_games`

Output:
- `data/analysis/synergy_matrix.csv`

## Hero-vs-Hero and Team Composition (`src/match_predictor.py`)
### Hero-vs-Hero matrix
For cross-team pairings `(hero_a, hero_b)`:
- Track games and wins for each ordered pair
- `winrate = wins / games`

Output:
- `data/analysis/hero_vs_hero_matrix.csv`

### Team compositions
For each unique sorted 6-hero team composition:
- Track games and wins
- `winrate = wins / games`

Output:
- `data/analysis/team_compositions.csv`

## Counter Matrix (`src/counter_engine.py`)
Derived from hero-vs-hero matrix:
- `counter_score = winrate - 0.5`

Interpretation:
- Positive: favorable matchup
- Negative: unfavorable matchup
- Near zero: neutral

Output:
- `data/analysis/counter_matrix.csv`

## Meta Analysis (`src/meta_analyzer.py`)
First computes hero pick and win rates from processed matches, then combines with average synergy and counter performance.

### Pick and win rates
- `pickrate = picks / total_match_sides`
- `winrate = wins / picks`

### Composite meta score
`meta_score =`
- `(winrate * 0.5)`
- `+ (pickrate * 0.25)`
- `+ (synergy_score * 0.15)`
- `+ (counter_score * 0.10)`

Outputs:
- `data/meta/hero_pickrates.csv`
- `data/meta/hero_winrates.csv`
- `data/meta/hero_meta_scores.csv`

## Team Strength (`src/team_analyzer.py`)
Heuristic role-bias score by composition diversity and balance. Role assignment is driven by `config/hero_metadata.json` — no hardcoded hero-name lists.

Accepted role buckets: `tank`, `carry`, `support`, `initiator`, `assassin`, `flex`.
Any hero whose metadata role is empty, unrecognised, or `unknown` is treated as `flex`.

High-level idea:
- Reward role diversity
- Penalize over-concentration in one role bucket

Output:
- `data/analysis/team_scores.csv`

## Draft Recommendations (`src/draft_engine.py`)
Scores candidate heroes not already picked/banned contextually.

For candidate hero:
- Base meta component
- Ally synergy component
- Enemy counter component

Formula:
- `score = base*0.6 + ally_synergy*0.25 + enemy_counter*0.15`

Output:
- `data/analysis/draft_recommendations.csv`

## Matchup Predictions (`src/match_predictor.py`)
Per historical match, estimate Team A win probability from weighted factors:
- Hero base win rates
- In-team synergy
- Counter interaction versus enemy lineup
- Hero-vs-hero matrix score
- Team composition historical win rate

Then adjusted by rank context factor derived from `player_ranks`.

Output:
- `data/analysis/matchup_predictions.csv`
