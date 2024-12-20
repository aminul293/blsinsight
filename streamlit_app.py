import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing

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
    "CES2000000007": "Construction Employment"
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

    # Line Chart with Log Scale Adjustment
    st.subheader("Trends Over Time")
    fig_line = px.line(
        df, x="date", y="value", color="seriesName",
        title="Trends Over Time",
        labels={"value": "Value", "date": "Date", "seriesName": "Series"},
    )
    fig_line.update_yaxes(title="Value (Adjusted Scale)", showgrid=True, range=[0, max(df['value'].max() * 1.1, 10000)])
    st.plotly_chart(fig_line)

    # Pie Chart
    st.subheader("Proportions of Latest Data")
    latest_date = df['date'].max()
    df_latest = df[df['date'] == latest_date]
    fig_pie = px.pie(
        df_latest, names="seriesName", values="value",
        title=f"Proportions of Latest Data (Date: {latest_date})"
    )
    st.plotly_chart(fig_pie)

    # Month-over-Month Change Bar Chart
    st.subheader("Month-over-Month Change")
    df['mom_change'] = df.groupby('seriesID')['value'].pct_change() * 100
    fig_mom = px.bar(
        df, x="date", y="mom_change", color="seriesName",
        title="Month-over-Month Change (%)",
        labels={"mom_change": "Change (%)"}
    )
    st.plotly_chart(fig_mom)

    # Rolling Averages
    st.subheader("Rolling Averages")
    rolling_window = st.slider("Select Rolling Window (Months)", 1, 12, value=3)
    df['rolling_avg'] = df.groupby('seriesID')['value'].transform(lambda x: x.rolling(window=rolling_window).mean())
    fig_rolling = px.line(
        df, x="date", y="rolling_avg", color="seriesName",
        title=f"Rolling Averages (Window Size = {rolling_window})",
        labels={"rolling_avg": "Rolling Average"}
    )
    st.plotly_chart(fig_rolling)

    # Bar Chart for Top Performers
    st.subheader("Top Performers")
    fig_bar = px.bar(
        df_latest, x="seriesName", y="value", color="seriesName",
        title="Top Performers by Value",
        labels={"value": "Value", "seriesName": "Series"}
    )
    fig_bar.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_bar)

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
        # Pivot the data for correlation
        corr_data = df.pivot(index='date', columns='seriesName', values='value')
        corr_matrix = corr_data.corr()

        # Use a valid Plotly color scale (e.g., 'viridis', 'plasma', etc.)
        fig_corr = px.imshow(
            corr_matrix, 
            text_auto=True, 
            color_continuous_scale="viridis",  # Updated to a valid color scale
            title="Correlation Matrix of Series"
        )
        st.plotly_chart(fig_corr)
    else:
        st.info("Not enough series selected to generate a correlation heatmap.")


# Tab 5: Forecasting
# Tab 5: Forecasting
with tab5:
    st.subheader("Customizable Forecasting")
    
    # Step 1: Select series for forecasting
    forecast_series = st.selectbox("Select a Series for Forecasting", options=df['seriesName'].unique())
    forecast_periods = st.slider("Select Number of Months to Forecast", 1, 36, 12)
    
    # Filter data for the selected series
    forecast_df = df[df['seriesName'] == forecast_series].copy()
    forecast_df.set_index('date', inplace=True)
    
    # Step 2: Ensure sufficient data
    if len(forecast_df) >= 12:  # Ensure at least 12 months of data
        # Adjust seasonal_periods dynamically based on available data
        seasonal_periods = min(12, len(forecast_df) // 2)
        
        # Step 3: Initialize ExponentialSmoothing model
        model = ExponentialSmoothing(
            forecast_df['value'],
            trend="additive",
            seasonal="additive" if seasonal_periods >= 12 else None,  # Add seasonality only if sufficient data
            seasonal_periods=seasonal_periods
        )
        
        # Step 4: Fit the model
        fitted_model = model.fit()
        forecast = fitted_model.forecast(forecast_periods)
        
        # Step 5: Plot the forecast
        fig_forecast = px.line(
            forecast_df, y='value', x=forecast_df.index,
            title="Customizable Forecasting",
            labels={"value": "Value", "date": "Date"}
        )
        fig_forecast.add_scatter(x=forecast.index, y=forecast, mode='lines', name='Forecast')
        st.plotly_chart(fig_forecast)
    
    # Step 6: Handle insufficient data
    else:
        st.warning("Not enough data points for forecasting (minimum 12 months required).")

