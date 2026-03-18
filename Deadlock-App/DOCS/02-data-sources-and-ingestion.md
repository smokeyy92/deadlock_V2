# 02. Data Sources and Ingestion

## API Base
Base URL used by client:
- `https://api.deadlock-api.com`

Client implementation:
- `src/api_client.py`

## Endpoints Used
### SQL-backed datasets
- Heroes: SQL query `SELECT id, name FROM heroes ORDER BY id`
- Items: SQL query `SELECT id, name, cost, tier, type, slot_type FROM items ORDER BY id`

### Analytics endpoints
- `/v1/analytics/ability-order-stats`
- `/v1/analytics/hero-stats`
- `/v1/analytics/item-stats`

### Matches endpoint
- `/v1/matches/metadata` with parameters:
  - `min_unix_timestamp` (now - 14 days)
  - `min_average_badge=114`
  - `include_info=true`
  - `include_player_kda=true`
  - `order_by=start_time`
  - `order_direction=desc`
  - `limit=10000`

### Additional context endpoints
- `/v1/leaderboard/NAmerica`
- `/v1/patches`
- `/v1/builds`

## High-Tier Filtering Logic
Badge encoding convention used:
- First digits: rank tier
- Last digit: tier subdivision

Eternus 4 maps to badge `114`.

Match filtering behavior:
- Server-side filter uses `min_average_badge=114`
- Client keeps this competitive scope and has fallback handling when endpoint behavior changes

## Raw Data Storage
Raw payloads are written to `data/raw/*.json`.

Important files:
- `data/raw/heroes.json`
- `data/raw/abilities.json`
- `data/raw/items.json`
- `data/raw/matches.json`
- `data/raw/hero_stats.json`
- `data/raw/item_stats.json`
- `data/raw/patches.json`
- `data/raw/players.json`
- `data/raw/leaderboards.json`

## Match Normalization During Ingestion
For each match row, the client stores:
- `match_id`
- `timestamp`
- `duration`
- `team_a_heroes`, `team_b_heroes`
- `winner` (`team_a` or `team_b`)
- `hero_kills`, `hero_deaths`, `hero_assists`
- `player_ranks` (team badge context)

This is intentionally structured to support downstream analytics without repeated API calls.
