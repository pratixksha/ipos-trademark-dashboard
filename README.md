# Singapore trademark activity monitor — IPOS open data dashboard

A data pipeline and Streamlit dashboard for analyzing **trademark filing activity in Singapore** using **IPOS (Intellectual Property Office of Singapore) open data** from data.gov.sg.

The project transforms raw trademark filing statistics into a lightweight monitoring dashboard that highlights filing trends, concentration across trademark classes, and statistically unusual years worth investigating.

## What this project does

The dashboard tracks:

* **Yearly filing trends** — total trademark filings over time
* **Year-over-year change** — filing growth or decline
* **Trademark class concentration** — which classes account for the most filings
* **Class distribution** — filing volume across trademark classes
* **Anomaly detection** — years that deviate significantly from recent historical activity

The goal is not to predict filings, but to **identify changes and outliers** that may warrant further investigation.

## Data source

* **Dataset:** IPOS trademark filing statistics from data.gov.sg
* **Input file:** `TrademarksfiledinSingaporebyClasses.csv`
* **Storage:** SQLite (`data/processed/ipos.db`)

The dataset is **not included in this repository**. Download it from the IPOS data.gov.sg dataset page and place it in the project root before running the pipeline.

## Pipeline

```text
TrademarksfiledinSingaporebyClasses.csv
                ↓
scripts/import_aggregated.py
                ↓
cleaned filing dataset
                ↓
scripts/load_db.py
                ↓
SQLite database
                ↓
scripts/queries.py
                ↓
Streamlit dashboard
```

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate

python3 -m pip install -r requirements.txt

# Place TrademarksfiledinSingaporebyClasses.csv in the project root

python3 scripts/import_aggregated.py
python3 scripts/load_db.py
streamlit run app/app.py
```

Open the local Streamlit URL (typically `http://localhost:8501`).

## Methodology

### Anomaly detection

Anomalies are detected using a **rolling mean and rolling standard deviation** (3-year window):

```python
rolling_mean = filing_count.rolling(window=3).mean()
rolling_std = filing_count.rolling(window=3).std()
z_score = (filing_count - rolling_mean) / rolling_std
is_anomaly = abs(z_score) > 2.0
```

A year is flagged when its filing volume differs substantially from the recent historical baseline. The approach is intentionally simple and explainable rather than model-driven.

## Project structure

```text
app/
  app.py                  # Streamlit dashboard

scripts/
  import_aggregated.py    # Convert source dataset into cleaned filing data
  load_db.py              # Load cleaned data into SQLite
  queries.py              # SQL queries and analytics

data/
  processed/              # Generated database (not tracked in Git)

requirements.txt
README.md
```

## Why I built this

I wanted to build a project that combines **data engineering, SQL analytics, and visualization** on a real government dataset.

The interesting part of the project is the **pipeline**: ingesting external data, transforming it into a queryable database, computing explainable analytics, and presenting the results through an interactive dashboard.

## Tech stack

* Python
* pandas
* SQLite
* Streamlit
* Plotly
