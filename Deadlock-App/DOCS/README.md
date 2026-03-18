# Deadlock Competitive Intelligence Toolkit - Team Documentation

This documentation package explains:
- What the application does
- What data it fetches
- How it transforms and stores data
- How each score or prediction is calculated
- How to run, debug, and present the system to stakeholders

## Audience
- Engineers extending the toolkit
- Analysts validating outputs
- Product or design teammates using the GUI

## Documentation Map
- [01. System Overview](01-system-overview.md)
- [02. Data Sources and Ingestion](02-data-sources-and-ingestion.md)
- [03. Data Processing and Calculations](03-data-processing-and-calculations.md)
- [04. GUI and Draft Workflow](04-gui-and-draft-workflow.md)
- [05. Outputs, Snapshot, and Troubleshooting](05-outputs-snapshot-troubleshooting.md)

## One-Paragraph Summary
The toolkit ingests Deadlock data from the public API, filters it to high-level competitive matches (Eternus 4+), builds normalized local datasets, computes synergy/counter/meta/prediction analytics, and exposes results in both CSV/Excel and a desktop draft GUI for pick-ban support.

## Key Guardrails
- Data source: `https://api.deadlock-api.com` only
- No web scraping
- Local deterministic processing
- Snapshot state is updated after pipeline actions
- Automatic rollback snapshots are created via `scripts/create_rollback_snapshot.ps1`
