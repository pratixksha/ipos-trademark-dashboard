"""
import_aggregated.py — Import an aggregated class-by-year CSV into the project's cleaned CSV.

This reads `TrademarksfiledinSingaporebyClasses.csv` (project root), which contains
`year, trademark_class, trademark_filings, rank` aggregated counts, and expands it
into a per-filing CSV compatible with `scripts/load_db.py` and the dashboard queries.

Usage:
    python3 scripts/import_aggregated.py
"""

import os
import pandas as pd

SRC = os.path.join(os.path.dirname(__file__), "..", "TrademarksfiledinSingaporebyClasses.csv")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "trademarks_clean.csv")


def main():
    if not os.path.exists(SRC):
        print(f"Aggregated CSV not found at {SRC}")
        return

    df = pd.read_csv(SRC)

    # Normalize column names if necessary
    df = df.rename(columns={
        'year': 'filing_year',
        'trademark_class': 'trademark_classes_str',
        'trademark_filings': 'filing_count'
    })

    # Convert class string to a consistent format (keep as-is)
    df['trademark_classes_str'] = df['trademark_classes_str'].astype(str)

    # Expand rows by filing_count to create one row per filing (synthetic rows)
    total = int(df['filing_count'].sum())
    print(f"Expanding aggregated data to ~{total:,} synthetic filing rows (this may take a moment)...")

    # Repeat rows
    df_expanded = df.loc[df.index.repeat(df['filing_count'])].reset_index(drop=True)

    # Build cleaned DataFrame with expected columns
    cleaned = pd.DataFrame({
        'application_number': [f'SYN-{i+1:06d}' for i in range(len(df_expanded))],
        'filing_date': pd.to_datetime(df_expanded['filing_year'].astype(int).astype(str) + '-01-01'),
        'filing_year': df_expanded['filing_year'].astype(int),
        'application_type': None,
        'trademark_type': None,
        'mark_status': None,
        'applicant_name': None,
        'applicant_country': None,
        'num_classes': 1,
        'trademark_classes_str': df_expanded['trademark_classes_str'],
    })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cleaned.to_csv(OUT, index=False)
    print(f"Wrote synthetic cleaned file: {OUT} ({len(cleaned):,} rows)")


if __name__ == '__main__':
    main()
