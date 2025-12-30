import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

def plot_total_asset(df):
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
