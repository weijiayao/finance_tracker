import streamlit as st
import pandas as pd
from datetime import datetime


def read_inputs():
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
         monthly_earned_income: float, annual_rate_percent: float, generate_plan: bool)
    """
    st.sidebar.subheader("Planned Finance Settings")

    # Defaults requested by user
    default_initial_asset = 3000.0
    default_initial_month = pd.to_datetime("2025-10-01")
    default_target_asset = 50000.0
    default_target_month = pd.to_datetime("2027-12-01")
    default_monthly_earned_income = 10000.0
    default_rate = 8.0
    default_income_increase_rate = 5.0

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
    monthly_earned_income = st.sidebar.number_input("Monthly salary", value=float(default_monthly_earned_income), step=100.0)
    annual_rate = st.sidebar.number_input("Average annual increase rate (%)", value=float(default_rate), step=0.1)
    annual_income_increase_rate = st.sidebar.number_input("Annual income increase rate (%)", value=float(default_income_increase_rate), step=0.1)

    generate = st.sidebar.button("Generate Plan")

    return (
        float(initial_asset_amount),
        initial_month.to_pydatetime(),
        float(target_asset_value),
        target_month.to_pydatetime(),
        float(monthly_earned_income),
        float(annual_rate),
        float(annual_income_increase_rate),
        bool(generate),
    )


def read_user_inputs():
    ( initial_asset_amount, 
    initial_asset_month, 
    target_asset_value, 
    target_time, 
    current_monthly_earned_income, 
    fc_annual_rate_percent,
    annual_income_increase_rate,
    generate_plan ) = read_inputs()
    
    # initialize "plan_settings" or plan settings update
    if "plan_settings" not in st.session_state or generate_plan:
        st.session_state["plan_settings"] = {
            "initial_asset_amount": float(initial_asset_amount),
            "initial_asset_month": pd.to_datetime(initial_asset_month),
            "target_asset_value": float(target_asset_value),
            "target_time": pd.to_datetime(target_time),
            "current_monthly_earned_income": float(current_monthly_earned_income),
            "fc_annual_rate_percent": float(fc_annual_rate_percent),
            "annual_income_increase_rate_percent": float(annual_income_increase_rate),
        }
        
    return generate_plan
        

def get_initial_asset():
        if "plan_settings" in st.session_state:
            ps = st.session_state["plan_settings"]
            return ps["initial_asset_amount"]

def get_initial_month():
        if "plan_settings" in st.session_state:
            ps = st.session_state["plan_settings"]
            return ps["initial_asset_month"].to_pydatetime() if hasattr(ps["initial_asset_month"], "to_pydatetime") else ps["initial_asset_month"]
        
def get_target_asset_value():
        if "plan_settings" in st.session_state:
            ps = st.session_state["plan_settings"]
            return ps["target_asset_value"]

def get_target_time():
        if "plan_settings" in st.session_state:
            ps = st.session_state["plan_settings"]
            return ps["target_time"].to_pydatetime() if hasattr(ps["target_time"], "to_pydatetime") else ps["target_time"]
def get_current_monthly_earned_income():
        if "plan_settings" in st.session_state:
            ps = st.session_state["plan_settings"]
            return ps["current_monthly_earned_income"]

def get_fc_annual_rate_percent():
        if "plan_settings" in st.session_state:
            ps = st.session_state["plan_settings"]
            return ps["fc_annual_rate_percent"]

def get_annual_income_increase_rate_percent():
        if "plan_settings" in st.session_state:
            ps = st.session_state["plan_settings"]
            return ps["annual_income_increase_rate_percent"]
        
def set_suggested_monthly_saving(value: float):
    """Set suggested monthly saving in session state."""
    st.session_state["suggested_monthly_saving"] = value
    

def write_outputs():
    """Render sidebar outputs for planned-finance settings."""
    if "suggested_monthly_saving" in st.session_state:
        st.sidebar.metric(
            label="Suggested monthly saving",
            value=f"${st.session_state['suggested_monthly_saving']:,.2f}",
        )