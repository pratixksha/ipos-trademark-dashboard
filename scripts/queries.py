
import sqlite3
import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "ipos.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def yearly_filing_trend() -> pd.DataFrame:
    """
    Total trademark filings per year.
    This is the base time series everything else (anomaly detection,
    YoY change) is built on.
    """
    query = """
        SELECT
            filing_year,
            COUNT(*) AS filing_count
        FROM trademarks
        WHERE filing_year IS NOT NULL
        GROUP BY filing_year
        ORDER BY filing_year
    """
    with get_connection() as conn:
        return pd.read_sql(query, conn)


def top_countries(limit: int = 10) -> pd.DataFrame:
    """
    Top applicant countries by total filing volume.
    Used to compute 'concentration risk' — what % of filings come from
    a small number of countries.
    """
    query = f"""
        SELECT
            applicant_country,
            COUNT(*) AS filing_count
        FROM trademarks
        WHERE applicant_country IS NOT NULL
        GROUP BY applicant_country
        ORDER BY filing_count DESC
        LIMIT {limit}
    """
    with get_connection() as conn:
        return pd.read_sql(query, conn)


def concentration_risk() -> float:
    """
    % of all filings that come from the top 5 applicant countries.
    A simple, explainable proxy for how concentrated filing activity is
    among a handful of countries 
    """
    total_query = "SELECT COUNT(*) AS total FROM trademarks WHERE applicant_country IS NOT NULL"
    top5_query = """
        SELECT SUM(filing_count) AS top5_total FROM (
            SELECT COUNT(*) AS filing_count
            FROM trademarks
            WHERE applicant_country IS NOT NULL
            GROUP BY applicant_country
            ORDER BY filing_count DESC
            LIMIT 5
        )
    """
    with get_connection() as conn:
        total = pd.read_sql(total_query, conn)["total"].iloc[0]
        top5 = pd.read_sql(top5_query, conn)["top5_total"].iloc[0]

    if not total:
        return 0.0
    return round(100 * top5 / total, 1)


def class_breakdown() -> pd.DataFrame:
    """
    Filing counts by trademark class string (a mark can span multiple
    classes, so this counts each class occurrence, not unique marks).
    """
    query = """
        SELECT
            trademark_classes_str,
            COUNT(*) AS filing_count
        FROM trademarks
        WHERE trademark_classes_str IS NOT NULL AND trademark_classes_str != ''
        GROUP BY trademark_classes_str
        ORDER BY filing_count DESC
        LIMIT 20
    """
    with get_connection() as conn:
        return pd.read_sql(query, conn)


def class_breakdown_by_year(year: int) -> pd.DataFrame:
    """
    Filing counts by trademark class string for a given year.
    """
    query = f"""
        SELECT
            trademark_classes_str,
            COUNT(*) AS filing_count
        FROM trademarks
        WHERE filing_year = {int(year)}
          AND trademark_classes_str IS NOT NULL
          AND trademark_classes_str != ''
        GROUP BY trademark_classes_str
        ORDER BY filing_count DESC
        LIMIT 20
    """
    with get_connection() as conn:
        return pd.read_sql(query, conn)


def mark_status_breakdown() -> pd.DataFrame:
    """Current status distribution (Registered, Expired, Removed, etc.)."""
    query = """
        SELECT
            mark_status,
            COUNT(*) AS count
        FROM trademarks
        WHERE mark_status IS NOT NULL
        GROUP BY mark_status
        ORDER BY count DESC
    """
    with get_connection() as conn:
        return pd.read_sql(query, conn)


def detect_anomalies(window: int = 3, threshold: float = 2.0) -> pd.DataFrame:
    """
    Flag years where filing volume deviates from a rolling mean by more
    than `threshold` standard deviations.
    """
    df = yearly_filing_trend()
    df["rolling_mean"] = df["filing_count"].rolling(window=window, min_periods=window).mean()
    df["rolling_std"] = df["filing_count"].rolling(window=window, min_periods=window).std()
    df["z_score"] = (df["filing_count"] - df["rolling_mean"]) / df["rolling_std"]
    df["is_anomaly"] = df["z_score"].abs() > threshold
    return df[df["is_anomaly"] == True][["filing_year", "filing_count", "rolling_mean", "z_score"]]


def yoy_change() -> pd.DataFrame:
    """Year-over-year % change in filing volume."""
    df = yearly_filing_trend()
    df["yoy_pct_change"] = df["filing_count"].pct_change() * 100
    return df
