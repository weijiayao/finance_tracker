import plotly.express as px
import streamlit as st
import pandas as pd


def render_plots(df):
    st.header("2. Year-to-Date Data Table & Plots")
    st.dataframe(df)

    # Salary vs Expense (+ asset_change, cash_transfer). If forecast total
    # asset is present, include it in the same chart so actual and forecast
    # series are visible together.
    base_series = [s for s in ["salary", "expense", "asset_change", "cash_transfer"] if s in df.columns]
    # include actual and forecast total asset if present
    asset_series = [s for s in ["total_asset", "fc_total_asset"] if s in df.columns]
    plot_series = base_series + asset_series

    # Ensure plotted columns are numeric and `month` is datetime so Plotly
    # Express can handle wide-form data without mixed-type errors.
    df_plot = df.copy()
    df_plot["month"] = pd.to_datetime(df_plot["month"])
    for col in plot_series:
        df_plot[col] = pd.to_numeric(df_plot.get(col), errors="coerce")

    fig1 = px.line(
        df_plot,
        x="month",
        y=plot_series,
        markers=True,
        title="Salary, Expense, asset_change (YTD) + Actual/Forecast Asset",
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Note: monthly saving and separate total_asset charts removed as requested.

def render_forecast(forecast_df):
    st.header("Forecasted Total Assets (Estimated)")
    st.dataframe(forecast_df)
    if "total_asset" in forecast_df.columns:
        fig = px.line(forecast_df, x="month", y="total_asset", markers=True, title="Forecasted Total Asset (Jan-Dec)")
        st.plotly_chart(fig, use_container_width=True)
