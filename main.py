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

if save:
    data.save_records_df(edited)

if reset:
    data.reset_records_df(year)

# --- Convert to DataFrame for plotting ---
df = data.get_records_df().copy()
if not df.empty:
    df = df.sort_values("month")
    df["saving"] = df["salary"] - df["expense"] + df["asset_change"]
    plots.render_plots(df)
else:
    st.info("No data yet. Edit the table above to add monthly values.")

st.markdown("---")
st.caption("Tip: Use the year selector in the sidebar to switch years. Next steps: add goal planning and budget suggestions.")
