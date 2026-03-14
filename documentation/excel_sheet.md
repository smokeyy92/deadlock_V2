# Deadlock Competitive Workbook

Workbook: [excel/deadlock_competitive_system.xlsx](/Users/tantig/Documents/deadlock/excel/deadlock_competitive_system.xlsx)

This workbook is a competitive Deadlock draft and coaching tool built around a 38-hero roster, 152 abilities, ability tags, role scoring formulas, hero pools, and a 6-player draft builder.

## Sheets

### Heroes

Primary hero database.

Columns:
- `Hero`: Hero name.
- `Category`: Dexerto hero class such as `Assassin`, `Brawler`, `Marksman`, or `Mystic`.
- `Baseline Role`: Imported from `excel/Character Roles.xlsx`.
- `Weapon`: Weapon style shown in the source data.
- `Tier`: Source page tier label.
- `A1` to `A4`: The hero's four abilities.

Use this sheet as the master list for hero lookups and dropdowns.

### Ability Tags

Ability-level tagging table.

Columns:
- `Hero`: Hero owning the ability.
- `Ability`: Ability name.
- `Tag`: Detailed tag such as `Damage`, `Pick`, `Tank`, `Utility`, `Engage`, or `Sustain`.
- `Tag Group`: Normalized group used by role formulas.
- `Description`: Ability description from the source page.

Notes:
- A single ability can have multiple tags.
- `Engage` is rolled into the `Pick` group for core role scoring.
- `Sustain` remains visible as its own tracking field and also informs lineup evaluation.

### Role Output

Formula-driven hero role scoring sheet.

Columns:
- `Hero`
- `Tank`
- `Pick`
- `Damage`
- `Utility`
- `Engage`
- `Sustain`
- `Role`

How it works:
- `Tank`, `Pick`, `Damage`, and `Utility` are calculated from ability tags plus the hero's baseline role.
- `Engage` and `Sustain` are counted directly from detailed tags.
- `Role` returns the highest of the four core role scores.

This is the main sheet to use when comparing hero coverage.

### Hero Pools

Quick pool views for team planning.

Sections:
- `Baseline Role Pools`: Heroes grouped by imported baseline role.
- `Derived Coverage Pools`: Heroes grouped by positive role coverage from `Role Output`.

Use this sheet to answer questions like:
- which heroes fit tank or utility needs
- which engage heroes a player can learn next
- which picks overlap too heavily in the same role lane

### Draft Builder

6-player lineup builder.

Inputs:
- Select one hero per player in cells `B3:B8`.

Outputs:
- Baseline role per pick
- Derived role per pick
- Tank / Pick / Damage / Utility / Engage / Sustain scores per pick
- Team summary on the right side

Summary checks:
- `Core Roles Covered?`
- `Engage + Sustain + Carry?`
- `Unique Heroes?`

This is the fastest sheet for testing a 6-hero composition.

### Notes

Source and metadata sheet.

Contains:
- data source notes
- role definition notes from `excel/Deadlock Roles.xlsx`

## Typical Workflow

1. Open `Draft Builder`.
2. Pick six heroes from the dropdowns.
3. Check whether the lineup covers `Tank`, `Pick`, `Damage`, and `Utility`.
4. Verify `Engage` and `Sustain` if you want a more complete competitive comp.
5. Use `Hero Pools` to find replacement heroes when a comp is missing coverage.

## Data Sources

- Hero list and ability descriptions: Dexerto Deadlock wiki hero pages.
- Baseline roles: `excel/Character Roles.xlsx`.
- Role definitions: `excel/Deadlock Roles.xlsx`.

## Regenerating The Workbook

Use:

```bash
python3 build_deadlock_competitive_workbook.py
```

This rebuilds:
- hero database
- ability tags
- role output formulas
- hero pools
- draft builder

## Limitations

- Ability tags are heuristic and generated from ability names and descriptions.
- Excel formulas are designed for modern Excel functions such as `XLOOKUP`, `FILTER`, `SORT`, and `UNIQUE`.
- If Dexerto changes page structure, the generator script may need a small update.
