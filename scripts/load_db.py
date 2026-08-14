"""
load_db.py — Load cleaned trademark data into a local SQLite database.

Usage:
    python scripts/load_db.py
"""

import os
import sqlite3
import pandas as pd

CLEAN_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "trademarks_clean.csv")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "ipos.db")


def load():
    df = pd.read_csv(CLEAN_PATH, parse_dates=["filing_date"])

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("trademarks", conn, if_exists="replace", index=False)

    # Helpful index for the date-range queries the dashboard will run
    conn.execute("CREATE INDEX IF NOT EXISTS idx_filing_year ON trademarks(filing_year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_applicant_country ON trademarks(applicant_country)")
    conn.commit()
    conn.close()

    print(f"Loaded {len(df)} rows into {DB_PATH} (table: trademarks)")


if __name__ == "__main__":
    load()
