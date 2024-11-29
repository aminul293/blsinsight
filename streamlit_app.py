import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# Load Data
try:
    df = pd.read_csv("data/bls_cleaned_data.csv")
except FileNotFoundError:
    st.error("The file 'bls_cleaned_data.csv' was not found. Please ensure you have processed the data.")
    st.stop()

# Map series IDs to human-readable names
series_descriptions = {
    "CEU0000000001": "Total Non-Farm Workers",
    "LNS14000000": "Unemployment Rates",
    "LNS11300000": "Labor Force Participation Rate"
}
df['seriesName'] = df['seriesID'].map(series_descriptions)

# Sidebar Filters
st.sidebar.header("Filters")
selected_series = st.sidebar.multiselect(
    "Select Series",
    options=df['seriesName'].unique(),
    default=["Total Non-Farm Workers", "Unemployment Rates"]
)
date_range = st.sidebar.date_input(
    "Select Date Range",
    [df['date'].min(), df['date'].max()]
)

# Filter Data
df = df[df['seriesName'].isin(selected_series)]
if len(date_range) == 2:
    df['date'] = pd.to_datetime(df['date'])
    df = df[(df['date'] >= pd.Timestamp(date_range[0])) & (df['date'] <= pd.Timestamp(date_range[1]))]

# Tabs for organization
tab1, tab2, tab3, tab4 = st.tabs(["Visualizations", "Raw Data", "Summary Insights", "Correlation Analysis"])

# Tab 1: Visualizations
with tab1:
    st.title("Labor Statistics Dashboard")

    # Comparison Line Chart
    st.subheader("Trends Over Time")
    fig_comparison = px.line(
        df, x="date", y="value", color="seriesName",
        title="Comparison of Labor Statistics Over Time",
        labels={"value": "Value", "seriesName": "Series"}
    )
    st.plotly_chart(fig_comparison)

    # Month-over-Month Change Bar Chart
    st.subheader("Month-over-Month Percentage Change")
    df['mom_change'] = df.groupby('seriesID')['value'].pct_change() * 100
    fig_mom = px.bar(
        df, x="date", y="mom_change", color="seriesName",
        title="Month-over-Month Change",
        labels={"mom_change": "MoM Change (%)"}
    )
    st.plotly_chart(fig_mom)

    # Annual Trends Area Plot
    st.subheader("Annual Trends")
    df['year'] = df['date'].dt.year
    fig_area = px.area(
        df, x="year", y="value", color="seriesName",
        title="Annual Data Trends",
        labels={"value": "Value", "year": "Year"}
    )
    st.plotly_chart(fig_area)

# Tab 2: Raw Data
with tab2:
    st.subheader("Raw Data")
    st.dataframe(df)

    # Download Filtered Data
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name="filtered_data.csv",
        mime="text/csv"
    )

# Tab 3: Summary Insights
with tab3:
    st.subheader("Key Performance Indicators")
    if len(df) > 0:
        latest_value = df[df['date'] == df['date'].max()]
        st.metric("Latest Value", f"{latest_value['value'].iloc[0]:,.2f}")
        st.metric("Highest Value", f"{df['value'].max():,.2f}")
        st.metric("Average Value", f"{df['value'].mean():,.2f}")

    st.subheader("Summary Statistics")
    st.write(f"Total: {df['value'].sum():,.2f}")
    st.write(f"Maximum: {df['value'].max():,.2f}")
    st.write(f"Minimum: {df['value'].min():,.2f}")

# Tab 4: Correlation Analysis
with tab4:
    st.subheader("Correlation Heatmap")
    if len(selected_series) > 1:
        # Pivot the data for correlation
        corr_data = df.pivot(index='date', columns='seriesName', values='value')
        corr_matrix = corr_data.corr()

        # Plot using seaborn
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)
    else:
        st.info("Select multiple series to view correlation analysis.")
