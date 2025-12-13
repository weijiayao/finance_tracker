import streamlit as st
import pandas as pd
from datetime import datetime


def make_year_df(year: int) -> pd.DataFrame:
    months = [datetime(year, m, 1) for m in range(1, 13)]
    # Add `cash_transfer` alongside existing columns. `asset_change` already exists.
    df = pd.DataFrame({
        "month": months,
        "salary": [0.0] * 12,
        "expense": [0.0] * 12,
        "asset_change": [0.0] * 12,
        "cash_transfer": [0.0] * 12,
    })
    return df


def init_session_state(year: int):
    if "records_df" not in st.session_state:
        st.session_state.records_df = make_year_df(year)
        st.session_state.year_selected = year

    if st.session_state.get("year_selected") != year:
        st.session_state.records_df = make_year_df(year)
        st.session_state.year_selected = year


def get_records_df() -> pd.DataFrame:
    return st.session_state.records_df


def save_records_df(df: pd.DataFrame):
    st.session_state.records_df = df.copy()


def reset_records_df(year: int):
    st.session_state.records_df = make_year_df(year)
    st.session_state.year_selected = year
