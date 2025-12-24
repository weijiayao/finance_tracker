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
    # --- Forecasting ---
    # Get forecast settings from the sidebar
    (
        fc_monthly_salary,
        fc_monthly_expense,
        fc_annual_rate_percent,
    ) = ui.forecast_settings(default_salary=0.0, default_expense=0.0, default_rate=3.0)

    # Use the same initial asset amount selected in the main UI so forecast
    # and actuals share the same starting asset configuration.
    # `initial_asset_amount` comes from `ui.initial_asset_config` above.
    fc_initial_asset = float(initial_asset_amount)

    # Build month list for the selected year (Jan-Dec)
    from datetime import datetime
    months = [datetime(year, m, 1) for m in range(1, 13)]

    # Constant monthly contribution from forecast settings (forecast is separate from actuals)
    contrib = float(fc_monthly_salary) - float(fc_monthly_expense)
    contribs = [contrib] * 12

    # Compute forecasted total asset month-by-month with monthly compounding
    # Convert annual percent to decimal, then compute monthly rate
    # from the 12th root: (1 + annual_rate)^(1/12) - 1
    annual_rate = float(fc_annual_rate_percent) / 100.0
    rate_monthly = (1.0 + annual_rate) ** (1.0 / 12.0) - 1.0

    # Align forecast start to the selected `initial_asset_month` so forecasts
    # and recorded `total_asset` use the same initial asset anchor.
    import pandas as pd

    assets = [None] * 12
    # find index in months list where month >= initial_asset_month
    start_idx = next((i for i, m in enumerate(months) if m >= initial_asset_month), None)
    if start_idx is not None:
        asset = float(fc_initial_asset)
        # fill forecast values from start_idx onward
        for i in range(start_idx, 12):
            asset = asset * (1.0 + rate_monthly) + float(contribs[i])
            assets[i] = asset

    forecast_df = pd.DataFrame({"month": months, "contribution": contribs, "total_asset": assets})

    # Merge forecast columns into the year-to-date dataframe so the UI shows
    # actuals and forecast side-by-side. Forecast columns are prefixed with
    # `fc_` to avoid name collisions.
    fc_subset = forecast_df[["month", "contribution", "total_asset"]].rename(
        columns={"contribution": "fc_contribution", "total_asset": "fc_total_asset"}
    )

    # Ensure month types match and perform a left merge so months present in
    # `df` retain their rows and receive forecast columns when available.
    merged_df = pd.merge(df, fc_subset, on="month", how="left")

    # Render combined plots and table
    plots.render_plots(merged_df)
else:
    st.info("No data yet. Edit the table above to add monthly values.")

st.markdown("---")
st.caption("Tip: Use the year selector in the sidebar to switch years. Next steps: add goal planning and budget suggestions.")
