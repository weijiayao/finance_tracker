import streamlit as st
import pandas as pd
from datetime import datetime


def year_input(default_year: int) -> int:
    return st.sidebar.number_input("Year", min_value=2000, max_value=2100, value=default_year, step=1)


def render_editor(records_df: pd.DataFrame):
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
