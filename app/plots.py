import plotly.express as px
import streamlit as st


def render_plots(df):
    st.header("2. Year-to-Date Data Table & Plots")
    st.dataframe(df)

    # Salary vs Expense
    fig1 = px.line(df, x="month", y=["salary", "expense", "asset_change", "cash_transfer"], markers=True, title="Salary, Expense, asset_change (YTD)")
    st.plotly_chart(fig1, use_container_width=True)

    # Monthly Saving
    fig2 = px.bar(df, x="month", y="saving", title="Monthly Saving")
    st.plotly_chart(fig2, use_container_width=True)
    
    # Total Asset Over Time
    fig3 = px.bar(df, x="month", y="total_asset", title="Total Asset Over Time")
    st.plotly_chart(fig3, use_container_width=True)

def render_forecast(forecast_df):
    st.header("Forecasted Total Assets (Estimated)")
    st.dataframe(forecast_df)
    if "total_asset" in forecast_df.columns:
        fig = px.line(forecast_df, x="month", y="total_asset", markers=True, title="Forecasted Total Asset (Jan-Dec)")
        st.plotly_chart(fig, use_container_width=True)
