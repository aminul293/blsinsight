import streamlit as st
import pandas as pd
import plotly.express as px

# Load Data
df = pd.read_csv("data/bls_cleaned_data.csv")

# Sidebar Filters
st.sidebar.header("Filters")
selected_series = st.sidebar.multiselect("Select Series", options=df['seriesID'].unique())
selected_date_range = st.sidebar.date_input("Select Date Range", [])

# Filter Data
if selected_series:
    df = df[df['seriesID'].isin(selected_series)]
if selected_date_range:
    df = df[(df['date'] >= selected_date_range[0]) & (df['date'] <= selected_date_range[1])]

# Plot Data
st.title("Labor Statistics Dashboard")
fig = px.line(df, x="date", y="value", color="seriesID", title="Labor Statistics Trends")
st.plotly_chart(fig)
