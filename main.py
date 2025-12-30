import streamlit as st
from datetime import datetime
import pandas as pd
from typing import Optional

from app import data, ui, plots, finance_plan

import altair as alt
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
st.title("Simple Monthly Finance Tracker")


def generate_planned_finance(
    current_monthly_salary: float,
    initial_asset: float,
    initial_time: datetime,
    target_asset_value: float,
    target_time: datetime,
    annual_return_rate_percent: float,
    generate: bool,
) -> pd.DataFrame:
    """Return a DataFrame with planned monthly projection from initial_time to target_time.

    Columns: `month`, `fc_total_asset`, `monthly_saving`, `cumulative_saving`, `suggested_expense`.
    If `generate` is False, returns an empty DataFrame.
    """
    if not generate:
        return pd.DataFrame(columns=["month", "total_asset_plan", "monthly_saving_plan", "cumulative_saving_plan", "suggested_expense_plan"]) 

    # Calculate required monthly saving and suggested expense
    pmt, suggested_expense = finance_plan.calculate_monthly_saving(
        current_monthly_salary=current_monthly_salary,
        initial_asset=initial_asset,
        initial_time=initial_time,
        target_asset_value=target_asset_value,
        target_time=target_time,
        annual_return_rate_percent=annual_return_rate_percent,
    )

    plan_df = finance_plan.generate_plan_projection(
        initial_asset=initial_asset,
        initial_time=initial_time,
        monthly_saving=pmt,
        target_time=target_time,
        annual_return_rate_percent=annual_return_rate_percent,
    )

    # Add suggested_expense as constant column and rename plan columns with suffix
    if not plan_df.empty:
        plan_df = plan_df.copy()
        plan_df["suggested_expense"] = float(suggested_expense)
    return plan_df


def real_finance_ui(initial_year: Optional[int] = None) -> tuple:
    """Render UI for real finance tracking and persist edits to session state.

    Returns:
        (records_df, edited_flag)
    """
    # Initialize session state for given year (used only for storage grouping)
    # If no year provided, default to current year.
    year = initial_year or datetime.today().year
    data.init_session_state(year)

    # Editor UI
    records_df = data.get_records_df()
    edited, save, reset = ui.user_input_table(records_df)

    if save:
        data.save_records_df(edited)

    if reset:
        data.reset_records_df(year)

    return data.get_records_df().copy(), bool(save)


def merge_real_into_plan(plan_df: pd.DataFrame, records_df: pd.DataFrame, initial_asset_month: datetime, initial_asset_amount: float) -> pd.DataFrame:
    """Add real `_real` columns directly into `plan_df` by aligning on `month`.

    If `plan_df` is empty, a timeseries is built from `records_df` months.
    """
    # Delegate to add_real_finance which now operates in-place on plan_df months
    merged = add_real_finance(plan_df, records_df, initial_asset_month, float(initial_asset_amount))
    return merged


def add_real_finance(plan_df: pd.DataFrame, records_df: pd.DataFrame, initial_asset_month: datetime, initial_asset_amount: float) -> pd.DataFrame:
    """Merge real records into a timeline that covers both real and planned months.

    Returns a DataFrame with a common `month` column and both real columns
    (`salary`, `expense`, `asset_change`, `cash_transfer`, `saving`, `total_asset`)
    and planned columns (`fc_total_asset`, `monthly_saving`, `cumulative_saving`, `suggested_expense`).
    """
    # Work from copies
    plan = plan_df.copy()
    records = records_df.copy()

    # Normalize month columns to first-day timestamps
    if not plan.empty:
        plan["month"] = pd.to_datetime(plan["month"]).dt.to_period("M").dt.to_timestamp()

    if not records.empty:
        records["month"] = pd.to_datetime(records["month"]).dt.to_period("M").dt.to_timestamp()

    # If no plan months (user didn't generate), build plan timeline from records
    if plan.empty:
        if records.empty:
            return pd.DataFrame()
        months = records["month"].sort_values().unique()
        plan = pd.DataFrame({"month": months})

    # Merge real records fields onto plan by month
    real_fields = ["salary", "expense", "asset_change", "cash_transfer"]
    # Prepare records subset (if missing columns, create zeros)
    rec_subset = records[["month"] + [c for c in real_fields if c in records.columns]].copy()
    for c in real_fields:
        if c not in rec_subset.columns:
            rec_subset[c] = 0.0

    merged = plan.merge(rec_subset, on="month", how="left")

    # Rename real columns with suffix and coerce numeric
    for c in real_fields:
        merged[c] = pd.to_numeric(merged.get(c), errors="coerce").fillna(0.0)
        merged = merged.rename(columns={c: f"{c}_real"})

    # compute saving_real
    merged["saving_real"] = (
        merged["salary_real"] - merged["expense_real"] + merged["asset_change_real"] + merged["cash_transfer_real"]
    )

    # compute total_asset_real starting from initial_asset_month if provided
    merged["total_asset_real"] = None
    try:
        start_idx = next((i for i, m in enumerate(merged["month"]) if m >= pd.to_datetime(initial_asset_month).to_period("M").to_timestamp()), None)
    except Exception:
        start_idx = 0
    if start_idx is not None:
        cum = merged.loc[start_idx:, "saving_real"].cumsum().reset_index(drop=True)
        merged.loc[start_idx:, "total_asset_real"] = float(initial_asset_amount) + cum.values

    # Ensure plan columns use suffixed names (if plan had plan names already keep them)
    plan_rename_map = {}
    if "fc_total_asset" in merged.columns:
        plan_rename_map["fc_total_asset"] = "total_asset_plan"
    if "monthly_saving" in merged.columns:
        plan_rename_map["monthly_saving"] = "monthly_saving_plan"
    if "cumulative_saving" in merged.columns:
        plan_rename_map["cumulative_saving"] = "cumulative_saving_plan"
    if "suggested_expense" in merged.columns:
        plan_rename_map["suggested_expense"] = "suggested_expense_plan"
    if plan_rename_map:
        merged = merged.rename(columns=plan_rename_map)

    # If plan_df provided separate plan columns earlier (like total_asset_plan), keep them.
    for c in ["total_asset_plan", "monthly_saving_plan", "cumulative_saving_plan", "suggested_expense_plan"]:
        if c not in merged.columns:
            merged[c] = None

    return merged


def finance_plot(df: pd.DataFrame):
    """Plot the combined dataframe using existing plotting utilities."""
    plots.render_plots(df)

# update whole_df with the new plan_df
def update_whole_df(plan_df: pd.DataFrame):
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


# --- Main execution: read sidebar inputs, render real UI, build plan, merge and plot ---
# Read planned finance inputs from sidebar
(initial_asset_amount, initial_asset_month, target_asset_value, target_time, current_monthly_salary, fc_annual_rate_percent, generate_plan,) = ui.forecast_settings()

# Persist plan inputs so they survive reruns triggered by editing the table.
if generate_plan:
    st.session_state["plan_settings"] = {
        "initial_asset_amount": float(initial_asset_amount),
        "initial_asset_month": pd.to_datetime(initial_asset_month),
        "target_asset_value": float(target_asset_value),
        "target_time": pd.to_datetime(target_time),
        "current_monthly_salary": float(current_monthly_salary),
        "fc_annual_rate_percent": float(fc_annual_rate_percent),
    }
else:
    # If a plan has been generated previously and user interacts (e.g., edits table),
    # reuse the saved plan settings so the planned columns persist.
    if "plan_settings" in st.session_state:
        ps = st.session_state["plan_settings"]
        initial_asset_amount = ps["initial_asset_amount"]
        initial_asset_month = ps["initial_asset_month"].to_pydatetime() if hasattr(ps["initial_asset_month"], "to_pydatetime") else ps["initial_asset_month"]
        target_asset_value = ps["target_asset_value"]
        target_time = ps["target_time"].to_pydatetime() if hasattr(ps["target_time"], "to_pydatetime") else ps["target_time"]
        current_monthly_salary = ps["current_monthly_salary"]
        fc_annual_rate_percent = ps["fc_annual_rate_percent"]

# Initialize session state grouped by the initial month year (no separate year selector)
data.init_session_state(initial_asset_month.year)

# Edits to real records are now handled inside the second table (plots view).

# Build the planned finance DataFrame
# Validate initial/target months before generating plan
plan_df = pd.DataFrame()
if generate_plan:
    try:
        init_ts = pd.to_datetime(initial_asset_month)
        tgt_ts = pd.to_datetime(target_time)
        months_diff = (tgt_ts.year - init_ts.year) * 12 + (tgt_ts.month - init_ts.month)
        if months_diff <= 0:
            st.error("Target month must be after initial month (at least one month later).")
            generate_plan = False
        else:
            plan_df = generate_planned_finance(
                current_monthly_salary=current_monthly_salary,
                initial_asset=float(initial_asset_amount),
                initial_time=initial_asset_month,
                target_asset_value=target_asset_value,
                target_time=target_time,
                annual_return_rate_percent=fc_annual_rate_percent,
                generate=generate_plan,
            )
            update_whole_df(plan_df)
            
    except Exception as e:
        st.error(f"Failed to generate plan: {e}")
        plan_df = pd.DataFrame()
        
    
if "whole_df" in st.session_state:
    render_real_finance_editor(
        st.session_state["whole_df"],
        initial_asset_amount=float(initial_asset_amount),
    )


    df = st.session_state["whole_df"]

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("value:Q", title="Total Asset"),
            color=alt.Color("type:N", title=""),
            tooltip=["month:T", "value:Q", "type:N"]
        )
        .transform_fold(
            ["total_asset", "total_asset_plan"],
            as_=["type", "value"]
        )
    )

    st.altair_chart(chart, use_container_width=True)



