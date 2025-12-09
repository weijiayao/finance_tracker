import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Simple Monthly Finance Tracker")

# --- Helpers ---
def make_year_df(year: int) -> pd.DataFrame:
    months = [datetime(year, m, 1) for m in range(1, 13)]
    df = pd.DataFrame({"month": months, "salary": [0.0] * 12, "expense": [0.0] * 12})
    return df

# --- Year selection ---
today = datetime.today()
year = st.sidebar.number_input("Year", min_value=2000, max_value=2100, value=today.year, step=1)

# Initialize session state for the table and selected year
if "records_df" not in st.session_state:
    st.session_state.records_df = make_year_df(year)
    st.session_state.year_selected = year

if st.session_state.get("year_selected") != year:
    # If user changed the year, reset the table for the new year
    st.session_state.records_df = make_year_df(year)
    st.session_state.year_selected = year

st.header("1. Edit Monthly Earnings & Expenses")
st.markdown("Edit the `salary` and `expense` values for each month directly in the table below.")

# Use Streamlit's data editor to allow inline editing
try:
    edited = st.data_editor(st.session_state.records_df, use_container_width=True)
except Exception:
    # Fallback for older Streamlit versions
    edited = st.experimental_data_editor(st.session_state.records_df, use_container_width=True)

# Sanitize typed values
edited = edited.copy()
edited["salary"] = pd.to_numeric(edited["salary"], errors="coerce").fillna(0.0)
edited["expense"] = pd.to_numeric(edited["expense"], errors="coerce").fillna(0.0)
edited["month"] = pd.to_datetime(edited["month"])

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Save Table"):
        st.session_state.records_df = edited.copy()
        st.success("Table saved to session state.")
with col2:
    if st.button("Reset Table"):
        st.session_state.records_df = make_year_df(year)
        st.success("Table reset for selected year.")

# --- Convert to DataFrame for plotting ---
df = st.session_state.records_df.copy()
if not df.empty:
    df = df.sort_values("month")
    df["saving"] = df["salary"] - df["expense"]

    st.header("2. Year-to-Date Data Table & Plots")
    st.dataframe(df)

    # Salary vs Expense
    fig1 = px.line(df, x="month", y=["salary", "expense"], markers=True, title="Salary vs Expense (YTD)")
    st.plotly_chart(fig1, use_container_width=True)

    # Monthly Saving
    fig2 = px.bar(df, x="month", y="saving", title="Monthly Saving (Salary - Expense)")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No data yet. Edit the table above to add monthly values.")

st.markdown("---")
st.caption("Tip: Use the year selector in the sidebar to switch years. Next steps: add goal planning and budget suggestions.")
