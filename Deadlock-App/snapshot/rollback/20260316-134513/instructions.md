# GOD-TIER CODEX PROMPT — Deadlock Competitive Intelligence Toolkit (FULL API + MATCH MODEL + GUI)

You are a senior systems engineer building a deterministic local toolkit for the game Deadlock.

The toolkit performs:

1 Hero dataset generation  
2 Ability dataset generation  
3 Item dataset generation  
4 Match dataset generation  
5 Meta analysis  
6 Hero synergy modelling  
7 Counter modelling  
8 Draft recommendation  
9 Matchup win probability prediction  
10 Patch meta comparison  
11 Professional Draft Tool GUI  

The system must run locally on Windows.

All data must come from:

https://api.deadlock-api.com

Web scraping is forbidden.

---------------------------------------------------------------------

# PRIMARY DESIGN GOAL

Minimize Codex context usage.

Codex must read only one state file:

snapshot/state.json

This file represents the full project state.

---------------------------------------------------------------------

# SNAPSHOT SYSTEM

Each run generates:

snapshot/state.json

Example:

{
 "version": "4.0",
 "hero_count": 0,
 "ability_count": 0,
 "item_count": 0,
 "match_count": 0,
 "dataset_last_generated": "",
 "last_patch_detected": "",
 "dataset_files": [
   "deadlock_dataset.xlsx"
 ],
 "analysis_files": [
   "hero_meta_scores.csv",
   "synergy_matrix.csv",
   "counter_matrix.csv"
 ]
}

---------------------------------------------------------------------

# STRICT TOKEN GUARDRAILS

Allowed libraries:

requests  
pandas  
numpy  
openpyxl  
rich  
tqdm  
PySide6  

Do NOT add extra dependencies.

---------------------------------------------------------------------

# PROJECT STRUCTURE

deadlock-intel-toolkit/

snapshot/
state.json

config/
roles.json
hero_metadata.json
synergy_rules.json
counter_rules.json

data/
raw/
processed/
meta/
analysis/
exports/

assets/
heroes/

src/

main.py  
api_client.py  
dataset_builder.py  
exporter.py  

synergy_engine.py  
counter_engine.py  
draft_engine.py  
match_predictor.py  
meta_analyzer.py  
team_analyzer.py  

models.py  
snapshot_manager.py  
utils.py  

src/gui/

main_window.py
pipeline_panel.py
draft_timeline_panel.py
hero_selector.py
recommendation_panel.py
team_analysis_panel.py
dataset_status_panel.py
hero_icon_loader.py

scripts/
run_toolkit.bat

---------------------------------------------------------------------

# DATA SOURCE — DEADLOCK API

Base URL:

https://api.deadlock-api.com/v1/

Multiple endpoints must be combined.

---------------------------------------------------------------------

# HERO DATA SOURCES

The toolkit must combine multiple API sources.

1 HERO LIST

GET /heroes

Contains:

hero_id  
hero_name  
slug  

Save:

data/raw/heroes.json

---------------------------------------------------------------------

2 HERO ANALYTICS

GET /analytics/hero-stats

Contains:

pick_rate  
win_rate  
games  
avg_kills  
avg_deaths  
avg_assists  

Save:

data/raw/hero_stats.json

---------------------------------------------------------------------

3 HERO BUILDS

GET /builds

Contains:

hero  
skill_order  
item_build  

Used to infer abilities and builds.

Save:

data/raw/builds.json

---------------------------------------------------------------------

4 ITEMS

GET /items

Save:

data/raw/items.json

---------------------------------------------------------------------

5 PATCHES

GET /patches

Save:

data/raw/patches.json

---------------------------------------------------------------------

6 MATCH DATA

GET /matches

If deeper data needed:

GET /matches/{id}/metadata

Save:

data/raw/matches.json

---------------------------------------------------------------------

# HERO METADATA COMPLETION

The API does NOT provide complete hero metadata.

Additional metadata must come from:

config/hero_metadata.json

Example:

{
 "abrams": {
  "role": "tank",
  "tags": ["frontline","engage"],
  "abilities": [
   "Shoulder Charge",
   "Bunker Blast",
   "Fortify",
   "Siege Mode"
  ]
 }
}

Dataset builder must merge:

heroes endpoint  
hero stats endpoint  
hero_metadata.json  

---------------------------------------------------------------------

# DATASET BUILDER

File:

src/dataset_builder.py

Merge sources:

heroes.json  
hero_stats.json  
hero_metadata.json  

Output:

data/processed/heroes.json

Example hero:

{
 "id": 1,
 "name": "Abrams",
 "slug": "abrams",
 "role": "tank",
 "tags": ["frontline","engage"],
 "stats": {
   "winrate": 0.53,
   "pickrate": 0.31,
   "avg_kills": 7.2,
   "avg_deaths": 5.8,
   "avg_assists": 9.4
 },
 "abilities": [
   "Shoulder Charge",
   "Bunker Blast",
   "Fortify",
   "Siege Mode"
 ]
}

---------------------------------------------------------------------

# HERO SYNERGY ENGINE

File:

src/synergy_engine.py

Compute hero pair synergy using match data.

Output:

data/analysis/synergy_matrix.csv

---------------------------------------------------------------------

# HERO COUNTER ENGINE

File:

src/counter_engine.py

Compute counters using hero vs hero winrates.

Output:

data/analysis/counter_matrix.csv

---------------------------------------------------------------------

# MATCHUP ENGINE

File:

src/match_predictor.py

Compute:

hero_vs_hero_matrix.csv

Algorithm:

for hero_a in team_a  
for hero_b in team_b  

calculate winrate.

---------------------------------------------------------------------

# META ANALYZER

File:

src/meta_analyzer.py

meta_score =

(winrate * 0.5)  
+ (pickrate * 0.25)  
+ (synergy_score * 0.15)  
+ (counter_score * 0.10)

Output:

data/meta/hero_meta_scores.csv

---------------------------------------------------------------------

# DRAFT ENGINE

File:

src/draft_engine.py

Input:

ally picks  
enemy picks  

Return:

top 5 hero recommendations

---------------------------------------------------------------------

# TEAM ANALYZER

File:

src/team_analyzer.py

Compute team composition metrics:

Tank  
Carry  
Support  
Initiator  
Assassin  

Output:

team_strength_score

---------------------------------------------------------------------

# GUI SYSTEM — PRO DRAFT ANALYZER

Framework:

PySide6

GUI must run locally.

---------------------------------------------------------------------

# GUI MODULE STRUCTURE

src/gui/

main_window.py
pipeline_panel.py
draft_timeline_panel.py
hero_selector.py
recommendation_panel.py
team_analysis_panel.py
dataset_status_panel.py
hero_icon_loader.py

---------------------------------------------------------------------

# MAIN WINDOW

Layout:

Left panel  
Pipeline controls

Center panel  
Draft timeline

Right panel  
Recommendations

Bottom panel  
Team analysis

Window title:

Deadlock Draft Analyzer

---------------------------------------------------------------------

# PIPELINE PANEL

Buttons:

Extract Hero Data  
Compute Synergy Matrix  
Compute Counter Matrix  
Run Meta Analysis  
Export Excel Dataset  
Run Full Pipeline  

---------------------------------------------------------------------

# DRAFT TIMELINE PANEL

Columns:

STEP  
TEAM  
ACTION  

Buttons:

Confirm Action  
Undo Last Step  
Reset Draft  
Auto Best Pick  

---------------------------------------------------------------------

# HERO SELECTOR

Dropdown hero selector.

Source:

data/processed/heroes.json

Icons loaded from:

assets/heroes/{hero}.png

---------------------------------------------------------------------

# RECOMMENDATION PANEL

Tables:

Top Pick Recommendations

Columns:

Hero  
Synergy Score  
Counter Score  
Role Score  
Final Score  

Top Ban Targets

Columns:

Hero  
Meta  
Counter Potential  
Ban Score  

---------------------------------------------------------------------

# TEAM ANALYSIS PANEL

Display bars for:

Tank  
Carry  
Support  
Initiator  
Assassin  

Display:

Team Strength Score

---------------------------------------------------------------------

# GUI DATA FLOW

API  
↓  
Dataset Builder  
↓  
Analysis Engines  
↓  
GUI  

GUI must read precomputed datasets only.

---------------------------------------------------------------------

# CLI COMMANDS

python src/main.py api  
python src/main.py dataset  
python src/main.py synergy  
python src/main.py counters  
python src/main.py meta  
python src/main.py predict  
python src/main.py analyze  
python src/main.py export  
python src/main.py gui  
python src/main.py all  

---------------------------------------------------------------------

# APPLICATION FLOW

python src/main.py all

Steps:

1 pull API datasets  
2 merge hero metadata  
3 ingest match data  
4 compute synergy matrix  
5 compute counter matrix  
6 compute matchup matrix  
7 compute meta scores  
8 export Excel dataset  
9 update snapshot  

---------------------------------------------------------------------

# FINAL OUTPUT

data/processed/heroes.json  
data/meta/hero_meta_scores.csv  
data/analysis/synergy_matrix.csv  
data/analysis/counter_matrix.csv  
data/analysis/hero_vs_hero_matrix.csv  
data/analysis/draft_recommendations.csv  
data/exports/deadlock_dataset.xlsx  

snapshot/state.json

---------------------------------------------------------------------

# ABSOLUTE RESTRICTIONS

Do NOT add:

databases  
web servers  
scrapers  

Only Deadlock API + metadata config.

---------------------------------------------------------------------

OUTPUT REQUIREMENT

Do NOT output explanations.

Only generate Python code for the project files.

# END PROMPT