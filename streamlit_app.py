import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import io

# Load Data
try:
    df = pd.read_csv("data/bls_cleaned_data.csv")
    df['date'] = pd.to_datetime(df['date'], errors='coerce')  # Ensure date is in datetime format
    if df['date'].isnull().any():
        raise ValueError("The 'date' column contains invalid or missing values.")
except FileNotFoundError:
    st.error("The file 'bls_cleaned_data.csv' was not found. Please ensure you have processed the data.")
    st.stop()
except ValueError as e:
    st.error(str(e))
    st.stop()

# Map series IDs to human-readable names
series_descriptions = {
    "CEU0000000001": "Total Non-Farm Workers",
    "LNS14000000": "Unemployment Rates",
    "LNS11300000": "Labor Force Participation Rate",
    "CES0500000003": "Average Hourly Earnings",
    "LNS12000000": "Employment Population Ratio",
    "CES3000000001": "Total Manufacturing Employment"
}
df['seriesName'] = df['seriesID'].map(series_descriptions)

# Sidebar Filters
st.sidebar.header("Filters")
selected_series = st.sidebar.multiselect(
    "Select Series",
    options=df['seriesName'].unique(),
    default=["Total Non-Farm Workers", "Unemployment Rates"]
)
default_start_date = df['date'].min() if not df['date'].isnull().all() else pd.Timestamp("2022-01-01")
default_end_date = df['date'].max() if not df['date'].isnull().all() else pd.Timestamp("2024-12-31")
date_range = st.sidebar.date_input(
    "Select Date Range",
    [default_start_date, default_end_date]
)

# Filter Data
df = df[df['seriesName'].isin(selected_series)]
if len(date_range) == 2:
    df = df[(df['date'] >= pd.Timestamp(date_range[0])) & (df['date'] <= pd.Timestamp(date_range[1]))]

# Tabs for organization
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Visualizations", "Raw Data", "Summary Insights", "Correlation Analysis", "Forecasting"])

# Tab 1: Visualizations
with tab1:
    st.title("Labor Statistics Dashboard")

    # Enhanced Line Chart
    st.subheader("Enhanced Trends Over Time")
    fig_enhanced = px.line(
        df, x="date", y="value", color="seriesName",
        title="Enhanced Trends Over Time",
        labels={"value": "Value", "date": "Date", "seriesName": "Series"},
        hover_data={"value": ":.2f", "seriesName": True}
    )
    fig_enhanced.update_layout(hovermode="x unified")
    st.plotly_chart(fig_enhanced)

    # Histogram for Distribution
    st.subheader("Value Distribution (Histogram)")
    fig_histogram = px.histogram(
        df, x="value", color="seriesName",
        title="Value Distribution by Series",
        labels={"value": "Value", "seriesName": "Series"},
        marginal="box"  # Adds a box plot to the histogram
    )
    st.plotly_chart(fig_histogram)

    # Moving Average
    st.subheader("Time-Weighted Moving Average")
    window_size = st.slider("Select Moving Average Window (Months)", 1, 12, value=3)
    df['moving_average'] = df.groupby('seriesID')['value'].transform(lambda x: x.rolling(window=window_size).mean())
    fig_ma = px.line(
        df, x="date", y="moving_average", color="seriesName",
        title=f"Moving Average (Window Size = {window_size})",
        labels={"moving_average": "Moving Average"}
    )
    st.plotly_chart(fig_ma)

    # Bubble Chart
    st.subheader("Bubble Chart of Series Over Time")
    fig_bubble = px.scatter(
        df, x="date", y="value", size="value", color="seriesName",
        title="Bubble Chart of Series Over Time",
        labels={"value": "Value", "date": "Date", "seriesName": "Series"}
    )
    st.plotly_chart(fig_bubble)

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
    st.subheader("Interactive Correlation Heatmap")
    if len(selected_series) > 1:
        corr_data = df.pivot(index='date', columns='seriesName', values='value')
        corr_matrix = corr_data.corr()

        fig_corr = px.imshow(
            corr_matrix, 
            text_auto=True, 
            color_continuous_scale="Viridis",  # Fixed the colorscale issue
            title="Correlation Matrix of Series"
        )
        st.plotly_chart(fig_corr)

    st.subheader("Scatter Plot Matrix")
    fig_scatter_matrix = px.scatter_matrix(
        df, dimensions=["value"], color="seriesName",
        title="Scatter Plot Matrix of Values",
        labels={"value": "Value"}
    )
    st.plotly_chart(fig_scatter_matrix)

# Tab 5: Forecasting
with tab5:
    st.subheader("Customizable Forecasting")
    forecast_series = st.selectbox("Select a Series for Forecasting", options=df['seriesName'].unique())
    forecast_periods = st.slider("Select Number of Months to Forecast", 1, 36, 12)

    forecast_df = df[df['seriesName'] == forecast_series].copy()
    forecast_df.set_index('date', inplace=True)

    if len(forecast_df) > 12:
        model = ExponentialSmoothing(
            forecast_df['value'], trend="additive", seasonal="additive", seasonal_periods=12
        )
        fitted_model = model.fit()
        forecast = fitted_model.forecast(forecast_periods)

        # Plot forecast
        fig_forecast = px.line(forecast_df, y='value', x=forecast_df.index, title="Customizable Forecasting")
        fig_forecast.add_scatter(x=forecast.index, y=forecast, mode='lines', name='Forecast')
        st.plotly_chart(fig_forecast)
    else:
        st.info("Not enough data points for forecasting (minimum 12 months required).")
