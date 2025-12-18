import streamlit as st
from datetime import datetime

from app import data, ui, plots


st.set_page_config(layout="wide")
st.title("Simple Monthly Finance Tracker")

# --- Year selection via UI ---
today = datetime.today()
year = ui.year_input(today.year)

# Initialize and manage session state
data.init_session_state(year)

# Editor UI
records_df = data.get_records_df()
edited, save, reset = ui.render_editor(records_df)

# Initial asset configuration (amount + month)
initial_asset_amount, initial_asset_month = ui.initial_asset_config(records_df, default_amount=0.0)

if save:
    data.save_records_df(edited)

if reset:
    data.reset_records_df(year)

# --- Convert to DataFrame for plotting ---
df = data.get_records_df().copy()
if not df.empty:
    # Sort and reset index to make positional operations predictable
    df = df.sort_values("month").reset_index(drop=True)

    # Compute saving including asset changes and cash transfers (if present)
    df["saving"] = (
        df.get("salary", 0.0)
        - df.get("expense", 0.0)
        + df.get("asset_change", 0.0)
        + df.get("cash_transfer", 0.0)
    )

    # Find the index of the selected initial asset month. If the exact month
    # isn't present, pick the first month after the selected month.
    matches = df.index[df["month"] == initial_asset_month].tolist()
    if matches:
        start_idx = matches[0]
    else:
        later = df.index[df["month"] >= initial_asset_month].tolist()
        start_idx = later[0] if later else len(df)

    # Cumulative saving starting at the configured initial asset month
    cum_from_initial = df["saving"].where(df.index >= start_idx).cumsum()

    # total_asset is only defined from start_idx onward
    df["total_asset"] = None
    if start_idx < len(df):
        df.loc[df.index >= start_idx, "total_asset"] = (
            initial_asset_amount + cum_from_initial[df.index >= start_idx]
        )

    plots.render_plots(df)
    # --- Forecasting ---
    # Get forecast settings from the sidebar
    (
        fc_monthly_salary,
        fc_monthly_expense,
        fc_initial_asset,
        fc_annual_rate_percent,
    ) = ui.forecast_settings(default_salary=0.0, default_expense=0.0, default_initial=0.0, default_rate=3.0)

    # Build month list for the selected year (Jan-Dec)
    from datetime import datetime
    months = [datetime(year, m, 1) for m in range(1, 13)]

    # Constant monthly contribution from forecast settings (forecast is separate from actuals)
    contrib = float(fc_monthly_salary) - float(fc_monthly_expense)
    contribs = [contrib] * 12

    # Compute forecasted total asset month-by-month with monthly compounding
    rate_monthly = float(fc_annual_rate_percent) / 100.0 / 12.0
    assets = []
    asset = float(fc_initial_asset)
    for c in contribs:
        asset = asset * (1.0 + rate_monthly) + float(c)
        assets.append(asset)

    import pandas as pd

    forecast_df = pd.DataFrame({"month": months, "contribution": contribs, "total_asset": assets})
    plots.render_forecast(forecast_df)
else:
    st.info("No data yet. Edit the table above to add monthly values.")

st.markdown("---")
st.caption("Tip: Use the year selector in the sidebar to switch years. Next steps: add goal planning and budget suggestions.")
