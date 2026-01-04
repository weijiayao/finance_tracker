import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

def plot_total_asset(df):
    # --- decide time scale based on buttons ---
    # Init state
    if "show_full_timeline" not in st.session_state:
        st.session_state.show_full_timeline = False

    left, center, right = st.columns([1, 2, 1])

    with center:
        btn1, btn2 = st.columns(2)

        with btn1:
            if st.button("Show first 12 months"):
                st.session_state.show_full_timeline = False

        with btn2:
            if st.button("Show full timeline"):
                st.session_state.show_full_timeline = True
        
    # Filter dataframe
    if st.session_state.show_full_timeline:
        plot_df = df
    else:
        plot_df = df.iloc[:12]   # first 12 months
    
    # --- create plots ---
    chart = (
        alt.Chart(plot_df)
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
    

    
    
    
