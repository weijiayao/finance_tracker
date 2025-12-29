import plotly.express as px
import streamlit as st
import pandas as pd
from app import data
from datetime import datetime


def render_plots(df):
    st.header("2. Year-to-Date Data Table & Plots")

    # Render a single combined editable table that contains both planned and
    # real columns. We will only persist real columns back to session state
    # when the user clicks Save Table.
    edit_df = df.copy()
    # Ensure month is a timestamp at month start for consistent merging
    edit_df["month"] = pd.to_datetime(edit_df["month"]).dt.to_period("M").dt.to_timestamp()

    st.markdown("Edit the table below. Planned columns are shown for reference; only real columns will be saved when you click Save Table.")
    try:
        edited = st.data_editor(edit_df, use_container_width=True)
    except Exception:
        edited = st.experimental_data_editor(edit_df, use_container_width=True)

    # sanitize and extract real columns
    edited = edited.copy()
    real_cols = ["salary_real", "expense_real", "asset_change_real", "cash_transfer_real"]
    for c in real_cols:
        if c in edited.columns:
            edited[c] = pd.to_numeric(edited[c], errors="coerce").fillna(0.0)
        else:
            # ensure column exists so save logic is simple
            edited[c] = 0.0

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Save Table"):
            rec = pd.DataFrame({
                "month": edited["month"],
                "salary": edited.get("salary_real", 0.0),
                "expense": edited.get("expense_real", 0.0),
                "asset_change": edited.get("asset_change_real", 0.0),
                "cash_transfer": edited.get("cash_transfer_real", 0.0),
            })
            # Convert month to first-day timestamps for storage
            rec["month"] = pd.to_datetime(rec["month"]).dt.to_period("M").dt.to_timestamp()
            data.save_records_df(rec)
            st.success("Table saved to session state.")
            # Rerun immediately so computed fields (saving_real, total_asset_real)
            # are recomputed and displayed in the updated table.
            try:
                st.experimental_rerun()
            except Exception:
                # Fallback for Streamlit versions without experimental_rerun
                try:
                    from streamlit.runtime.scriptrunner import RerunException

                    raise RerunException("rerun")
                except Exception:
                    # Last resort: set a session flag so the page reflects change
                    st.session_state["records_updated"] = True
    with col2:
        if st.button("Reset Table"):
            year = st.session_state.get("year_selected", datetime.today().year)
            data.reset_records_df(year)
            st.success("Table reset for selected year.")
            try:
                st.experimental_rerun()
            except Exception:
                try:
                    from streamlit.runtime.scriptrunner import RerunException

                    raise RerunException("rerun")
                except Exception:
                    st.session_state["records_updated"] = True

    st.markdown("---")

    # Only plot total asset series (planned vs real) as requested.
    plot_series = [s for s in ["total_asset_real", "total_asset_plan"] if s in df.columns]

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
        title="Total Asset: Real vs Planned",
    )
    # If planned/forecasted asset exists, limit x-axis to the span where
    # either actual `total_asset` or planned `fc_total_asset` are present.
    try:
        has_plan = "fc_total_asset" in df_plot.columns and df_plot["fc_total_asset"].notna().any()
        has_actual = "total_asset" in df_plot.columns and df_plot["total_asset"].notna().any()
        if has_plan or has_actual:
            mask = (df_plot["fc_total_asset"].notna() if has_plan else False) | (
                df_plot["total_asset"].notna() if has_actual else False
            )
            if mask.any():
                min_month = df_plot.loc[mask, "month"].min()
                max_month = df_plot.loc[mask, "month"].max()
                # Convert to ISO strings acceptable to Plotly
                fig1.update_xaxes(range=[min_month.strftime("%Y-%m-%d"), max_month.strftime("%Y-%m-%d")])
    except Exception:
        # If anything goes wrong setting range, fall back to full-year view.
        pass

    st.plotly_chart(fig1, use_container_width=True)

    # Note: monthly saving and separate total_asset charts removed as requested.

def render_forecast(forecast_df):
    st.header("Forecasted Total Assets (Estimated)")
    st.dataframe(forecast_df)
    if "total_asset" in forecast_df.columns:
        fig = px.line(forecast_df, x="month", y="total_asset", markers=True, title="Forecasted Total Asset (Jan-Dec)")
        st.plotly_chart(fig, use_container_width=True)
