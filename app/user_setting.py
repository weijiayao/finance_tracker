import streamlit as st
import pandas as pd
from datetime import datetime


def user_settings():
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
    default_initial_month = pd.to_datetime("2025-10-01")
    default_target_asset = 50000.0
    default_target_month = pd.to_datetime("2027-12-01")
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
