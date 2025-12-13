import plotly.express as px
import streamlit as st


def render_plots(df):
    st.header("2. Year-to-Date Data Table & Plots")
    st.dataframe(df)

    # Salary vs Expense
    fig1 = px.line(df, x="month", y=["salary", "expense", "asset_change", "cash_transfer"], markers=True, title="Salary, Expense, asset_change (YTD)")
    st.plotly_chart(fig1, use_container_width=True)

    # Monthly Saving
    fig2 = px.bar(df, x="month", y="saving", title="Monthly Saving (Salary - Expense)")
    st.plotly_chart(fig2, use_container_width=True)
