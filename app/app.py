"""
app.py — Streamlit dashboard for IPOS trademark filing analysis.

Run locally with:
    streamlit run app/app.py
"""

import os
import sys
import warnings
# Suppress Plotly deprecation message about using `config` for keyword args
warnings.filterwarnings(
    "ignore",
    message=r".*Use .*config.*instead.*",
)
import logging
# Reduce noisy Plotly/info logs that Surface deprecation messages
for logger_name in ("plotly", "plotly.io", "plotly.io._base_renderers"):
    logging.getLogger(logger_name).setLevel(logging.ERROR)
import streamlit as st
# Import Plotly while silencing noisy stdout/stderr messages from internal setup
import sys as _sys
import os as _os
_devnull = open(_os.devnull, "w")
_old_stdout, _old_stderr = _sys.stdout, _sys.stderr
_sys.stdout = _devnull
_sys.stderr = _devnull
import plotly.express as px
import plotly.graph_objects as go
_sys.stdout, _sys.stderr = _old_stdout, _old_stderr
_devnull.close()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from queries import (
    yearly_filing_trend,
    top_countries,
    concentration_risk,
    class_breakdown,
    mark_status_breakdown,
    detect_anomalies,
    yoy_change,
    class_breakdown_by_year,
)
import importlib
queries = importlib.import_module("queries")

st.set_page_config(page_title="IPOS Trademark Filing Trends", layout="wide")

st.title("Singapore Trademark Filing Trends (IPOS Open Data)")
st.caption(
    "Data source: IPOS Trade Mark Applications, data.gov.sg. "
    "Built as a portfolio project on IP filing/risk analysis."
)

# --- Summary stats row ---
trend_df = yearly_filing_trend()
yoy_df = yoy_change()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total filings analyzed", f"{trend_df['filing_count'].sum():,}")
with col2:
    latest_year = trend_df["filing_year"].max()
    latest_count = trend_df[trend_df["filing_year"] == latest_year]["filing_count"].iloc[0]
    st.metric(f"Filings in {int(latest_year)}", f"{latest_count:,}")
with col3:
    latest_yoy = yoy_df["yoy_pct_change"].iloc[-1] if len(yoy_df) > 1 else None
    st.metric("YoY change", f"{latest_yoy:.1f}%" if latest_yoy is not None else "N/A")
with col4:
    # Only show concentration if we have applicant country data
    try:
        cr = concentration_risk()
    except Exception:
        cr = 0.0
    st.metric("Top-5 country concentration", f"{cr}%" if cr else "N/A")

st.divider()

# --- Filing trend + anomalies ---
st.subheader("Filing volume over time")
anomalies_df = detect_anomalies()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=trend_df["filing_year"], y=trend_df["filing_count"],
    mode="lines+markers", name="Filings"
))
if not anomalies_df.empty:
    fig.add_trace(go.Scatter(
        x=anomalies_df["filing_year"], y=anomalies_df["filing_count"],
        mode="markers", name="Anomaly",
        marker=dict(size=14, color="red", symbol="x")
    ))
fig.update_layout(xaxis_title="Year", yaxis_title="Number of filings", height=400)
st.plotly_chart(fig, width='stretch')

if not anomalies_df.empty:
    with st.expander("Flagged anomalies — years that deviate >2 std devs from the 3-year rolling mean"):
        st.dataframe(anomalies_df, width='stretch')
        st.code(
            "-- Anomaly logic (see scripts/queries.py -> detect_anomalies)\n"
            "rolling_mean = filing_count.rolling(window=3).mean()\n"
            "rolling_std  = filing_count.rolling(window=3).std()\n"
            "z_score      = (filing_count - rolling_mean) / rolling_std\n"
            "is_anomaly   = abs(z_score) > 2.0",
            language="python"
        )
else:
    st.info("No anomalies detected in the current dataset (this sample is small — the full pull will show more).")

st.divider()

# --- Top classes (stacked for readability) ---
st.subheader("Top trademark classes — selected year")
years = list(trend_df["filing_year"].dropna().astype(int).unique())
selected_year = st.selectbox("Year", years, index=len(years) - 1)
classes_year_df = queries.class_breakdown_by_year(int(selected_year))
if classes_year_df.empty:
    st.info("No class data available for the selected year.")
else:
    fig2 = px.bar(classes_year_df, x="filing_count", y="trademark_classes_str", orientation="h")
    fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
    st.plotly_chart(fig2, width='stretch')

st.subheader("Top trademark classes — overall")
classes_df_overall = class_breakdown()
if classes_df_overall.empty:
    st.info("No class data available in the dataset.")
else:
    fig3 = px.bar(classes_df_overall, x="filing_count", y="trademark_classes_str", orientation="h")
    fig3.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
    st.plotly_chart(fig3, width='stretch')

st.divider()

st.subheader("Top trademark class combinations")
st.caption("Most common class combination a single application is filed under.")
classes_df = class_breakdown()
st.dataframe(classes_df, width='stretch')
