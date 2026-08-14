# Singapore Trademark Filing Trends — IPOS Open Data Dashboard

Lightweight Streamlit dashboard and pipeline for exploring trademark filing activity in Singapore. This repository ships with an aggregated CSV of trademark filings by year and class and provides tooling to convert that into the cleaned dataset used by the dashboard.

**Status:** ready to run locally with the provided CSV. The original `fetch.py`/`clean.py` pipeline has been deprecated in this copy — see Notes below.

## What this repo contains

- `TrademarksfiledinSingaporebyClasses.csv` — aggregated counts by `year` and `trademark_class` (the provided source)
- `scripts/import_aggregated.py` — converts the aggregated CSV into a per-filing cleaned CSV used by the app (creates synthetic per-filing rows)
- `scripts/load_db.py` — loads the cleaned CSV into `data/processed/ipos.db` (SQLite)
- `scripts/queries.py` — SQL queries used by the dashboard (yearly trends, class breakdowns, anomaly detection)
- `app/app.py` — Streamlit dashboard UI (uses Plotly to render charts)
- `data/processed/*` — generated cleaned CSV and SQLite DB after running the importer and loader
- `requirements.txt` — Python deps

## Quick start (recommended)

1. Create and activate a virtual environment (optional but recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt
```

3. Convert the aggregated CSV into the cleaned per-filing CSV and load the DB:

```bash
python3 scripts/import_aggregated.py
python3 scripts/load_db.py
```

4. Run the dashboard:

```bash
streamlit run app/app.py
```

Open the Local URL printed by Streamlit (usually http://localhost:8501).

## What the importer does

- `import_aggregated.py` expands each aggregated (year, class, count) row into synthetic per-filing rows so the rest of the pipeline (SQL queries, anomaly detection) can run without changing query logic.
- Synthetic rows include:
  - `filing_date`: set to `YYYY-01-01` (year start)
  - `trademark_classes_str`: copied from the aggregated CSV
  - `applicant_country`, `mark_status`, and other applicant-level fields: left empty (NULL)

## Important caveats

- Country and mark-status metrics are empty because the aggregated CSV does not include applicant-level metadata. The dashboard hides or annotates those charts when data is missing.
- Synthetic expansion is a convenience to make the SQL-based dashboard work; it does not recreate real per-application details. If you have a raw per-application CSV (with `applicant_country`, `mark_status`, and class arrays), import that instead for richer analysis.

## Anomaly detection

- The dashboard flags anomalies using a simple rolling mean + std approach (3-year rolling window, flag if |z| > 2). This is intentionally explainable; absence of a flagged anomaly means "no year exceeded the chosen threshold in the current data", not that nothing interesting exists.

## Contributing / next work

- Add a proper cleaning pipeline to parse raw API JSON -> normalized rows (if you re-enable the fetch flow).
- Add caching / pagination for the Streamlit UI if the dataset grows large.
- Add unit tests for key `scripts/queries.py` functions.

