import streamlit as st
from datetime import datetime
import pandas as pd
from typing import Optional
from app import plots, finance_plan, user_setting
import streamlit as st

# Designated columns
REAL_COLS = [
    "total_asset",
    "earned_income",
    "expense",
    "saving",
    "cumulative_saving",
    "investment_gain",
    "cumulative_investment_gain",
    "total_gain",
    "cumulative_total_gain",
]

DISPLAYED_COLS = [
    "month",
    "total_asset_plan",
    "total_asset",
    "earned_income",
    "expense",
    "saving",
    "cumulative_saving",
    "investment_gain",
    "cumulative_investment_gain",
    "total_gain",
    "cumulative_total_gain",
]

EDITABLE_COLS = ["total_asset", "earned_income", "expense"]

st.set_page_config(layout="wide")
st.title("Family Finance Tracker")

# init whole dataframe
def init_whole_df(plan_df: pd.DataFrame):
    """Initialize whole_df in session_state once."""
    if plan_df.empty:
        return

    whole_df = plan_df.copy()

    # Initialize real finance columns
    # user inputs
    whole_df["total_asset"] = pd.NA
    whole_df["earned_income"] = pd.NA
    whole_df["expense"] = pd.NA
    
    # outputs
    whole_df["saving"] = pd.NA
    whole_df["cumulative_saving"] = pd.NA
    whole_df["investment_gain"] = pd.NA
    whole_df["cumulative_investment_gain"] = pd.NA
    whole_df["total_gain"] = pd.NA
    whole_df["cumulative_total_gain"] = pd.NA
    
    
    # initialize all REAL_COLS to 0.0
    for col in REAL_COLS:
        whole_df[col] = 0.0

    st.session_state["whole_df"] = whole_df

def render_real_finance_editor(
    df: pd.DataFrame,
    initial_asset_amount: float,
):
    st.subheader("Update Real Finance")

    
    display_df = df[DISPLAYED_COLS]
    
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        num_rows="fixed",
        disabled=[
            c for c in display_df.columns if c not in EDITABLE_COLS
        ],
        key="real_finance_editor",
    )
    
    edited_df = edited_df[EDITABLE_COLS]

    if st.button("Update table"):
        updated_df = apply_real_finance_update(
            edited_df,
            initial_asset_amount,
        )
        
        # Patch only editable columns back
        whole_df = df.copy()
        current_month = pd.Timestamp.today().to_period("M").to_timestamp()
        month_mask = whole_df["month"] <= current_month
        # write back only REAL_COLS and designated months
        whole_df.loc[month_mask, REAL_COLS] = (updated_df.loc[month_mask, REAL_COLS])
    
        st.session_state["whole_df"] = whole_df
        st.success("Table updated!")  # Optional feedback
        # rerun the app to reflect changes
        st.rerun()

def apply_real_finance_update(
    df: pd.DataFrame,
    initial_asset_amount: float,
) -> pd.DataFrame:
    updated = df.copy()
    
    # saving
    updated["saving"] = updated["earned_income"] - updated["expense"]
    updated["cumulative_saving"] = updated["saving"].cumsum()
    # total gain
    updated["total_gain"] = updated["total_asset"].diff()
    updated.loc[0, "total_gain"] = updated.loc[0, "total_asset"] - initial_asset_amount
    updated["cumulative_total_gain"] = updated["total_gain"].cumsum()
    # investment gain
    updated["investment_gain"] = updated["total_gain"] - updated["saving"]
    updated["cumulative_investment_gain"] = updated["investment_gain"].cumsum()
    

    return updated

def generate_finance_plan():
    plan_df = pd.DataFrame()
    try:
        init_ts = pd.to_datetime(user_setting.get_user_setting_initial_month())
        tgt_ts = pd.to_datetime(user_setting.get_user_setting_target_time())
        months_diff = (tgt_ts.year - init_ts.year) * 12 + (tgt_ts.month - init_ts.month)
        if months_diff <= 0:
            st.error("Target month must be after initial month (at least one month later).")
        else:
            plan_df = finance_plan.generate_planned_finance(
                current_monthly_salary=user_setting.get_user_setting_current_monthly_salary(),
                initial_asset=float(user_setting.get_user_setting_initial_asset()),
                initial_time=user_setting.get_user_setting_initial_month(),
                target_asset_value=user_setting.get_user_setting_target_asset_value(),
                target_time=user_setting.get_user_setting_target_time(),
                annual_return_rate_percent=user_setting.get_user_setting_fc_annual_rate_percent(),
                generate=True,
            )
            
    except Exception as e:
        st.error(f"Failed to generate plan: {e}")
        plan_df = pd.DataFrame()
        
    return plan_df

# --- Main execution ---
# Read user settings
generate_plan = user_setting.read_user_setting()

# build finance plan dataframe
if generate_plan:
    plan_df = generate_finance_plan()
    # initialize whole dataframe if finance plan changed
    init_whole_df(plan_df)

# update data from table upon save behavior, and plot it
if "whole_df" in st.session_state:
    render_real_finance_editor(
        st.session_state["whole_df"],
        initial_asset_amount=float(user_setting.get_user_setting_initial_asset()),
    )
    plots.plot_total_asset(st.session_state["whole_df"])


