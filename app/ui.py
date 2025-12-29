import streamlit as st
import pandas as pd
from datetime import datetime


def year_input(default_year: int) -> int:
    return st.sidebar.number_input("Year", min_value=2000, max_value=2100, value=default_year, step=1)


def user_input_table(records_df: pd.DataFrame):
    st.header("1. Edit Monthly Earnings & Expenses")
    st.markdown("Edit the `salary` and `expense` values for each month directly in the table below.")
    # Render editable table using Streamlit's data editor.
    # Note: this returns a *copy* of the dataframe as edited by the user.
    # We catch the older API name as a fallback for older Streamlit versions.
    try:
        edited = st.data_editor(records_df, use_container_width=True)
    except Exception:
        edited = st.experimental_data_editor(records_df, use_container_width=True)

    # Sanitize typed values so downstream code can rely on consistent types.
    # - Keep `edited` as a separate copy so session state is not mutated here.
    # - Coerce salary/expense to numeric and fill NaNs with 0.0.
    # - Ensure `month` column is datetime so sorting/plotting works.
    edited = edited.copy()
    edited["salary"] = pd.to_numeric(edited["salary"], errors="coerce").fillna(0.0)
    edited["expense"] = pd.to_numeric(edited["expense"], errors="coerce").fillna(0.0)
    edited["asset_change"] = pd.to_numeric(edited["asset_change"], errors="coerce").fillna(0.0)
    edited["cash_transfer"] = pd.to_numeric(edited["cash_transfer"], errors="coerce").fillna(0.0)
    edited["month"] = pd.to_datetime(edited["month"])

    # Create two buttons: Save and Reset.
    # Important: These buttons only set flags (`save`/`reset`) returned to the
    # caller (`main.py`). The actual persistence (writing back to
    # `st.session_state`) is performed by the caller so we keep UI and state
    # management responsibilities separated.
    col1, col2 = st.columns([1, 1])
    save = False
    reset = False
    with col1:
        if st.button("Save Table"):
            save = True
            st.success("Table saved to session state.")
    with col2:
        if st.button("Reset Table"):
            reset = True
            st.success("Table reset for selected year.")

    # Return the sanitized edited dataframe and two boolean flags.
    return edited, save, reset

def initial_asset_config(records_df: pd.DataFrame, default_amount: float = 0.0):
    """Render sidebar controls to configure an initial asset value and the month it applies to.

    Returns:
        (initial_amount: float, initial_month: datetime)
    """
    # Build a list of month labels from the records so the user can pick a month.
    months = records_df["month"].dt.to_period("M").astype(str).tolist()
    # Default to the first month in the table
    default_idx = 0
    selected_label = st.sidebar.selectbox("Initial asset month", months, index=default_idx)
    initial_amount = st.sidebar.number_input("Initial asset amount", value=float(default_amount), step=100.0)

    # Convert the selected label (YYYY-MM) back to a Timestamp at first day of month
    initial_month = pd.to_datetime(selected_label + "-01")
    return float(initial_amount), initial_month


def forecast_settings():
    """Render sidebar controls for planned-finance settings using month pickers.

    Defaults:
      - initial asset: 3000
      - initial month: Dec 2025
      - target asset: 50000
      - target month: Dec 2028
      - monthly salary: 10000
      - annual increase rate: 8

    Returns:
        (initial_asset_amount: float, initial_month: datetime,
         target_asset_value: float, target_month: datetime,
         monthly_salary: float, annual_rate_percent: float, generate_plan: bool)
    """
    st.sidebar.subheader("Planned Finance Settings")

    # Defaults requested by user
    default_initial_asset = 3000.0
    default_initial_month = pd.to_datetime("2025-12-01")
    default_target_asset = 50000.0
    default_target_month = pd.to_datetime("2028-12-01")
    default_monthly_salary = 10000.0
    default_rate = 8.0

    initial_asset_amount = st.sidebar.number_input("Initial asset amount", value=float(default_initial_asset), step=100.0)

    # Build a list of month options (first day of month timestamps)
    years = list(range(2023, 2036))
    months = [pd.to_datetime(f"{y}-{m:02d}-01") for y in years for m in range(1, 13)]

    def fmt(d: pd.Timestamp) -> str:
        return d.strftime("%b %Y")

    # Select initial month
    initial_idx = months.index(default_initial_month) if default_initial_month in months else 0
    initial_month = st.sidebar.selectbox("Initial month", months, index=initial_idx, format_func=fmt)

    target_idx = months.index(default_target_month) if default_target_month in months else len(months) - 1
    target_month = st.sidebar.selectbox("Target month", months, index=target_idx, format_func=fmt)

    target_asset_value = st.sidebar.number_input("Target asset value", value=float(default_target_asset), step=100.0)
    monthly_salary = st.sidebar.number_input("Monthly salary", value=float(default_monthly_salary), step=100.0)
    annual_rate = st.sidebar.number_input("Average annual increase rate (%)", value=float(default_rate), step=0.1)

    generate = st.sidebar.button("Generate Plan")

    return (
        float(initial_asset_amount),
        initial_month.to_pydatetime(),
        float(target_asset_value),
        target_month.to_pydatetime(),
        float(monthly_salary),
        float(annual_rate),
        bool(generate),
    )
