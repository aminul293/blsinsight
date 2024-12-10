import streamlit as st
import pandas as pd
import plotly.express as px
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
    "CES9091000001": "Construction Employment",
    "LNS12000000": "Employment-Population Ratio"
}
df['seriesName'] = df['seriesID'].map(series_descriptions)

# Sidebar Filters
st.sidebar.header("Filters")
selected_series = st.sidebar.multiselect(
    "Select Series",
    options=df['seriesName'].unique(),
    default=df['seriesName'].unique()
)
date_range = st.sidebar.date_input(
    "Select Date Range",
    [df['date'].min(), df['date'].max()]
)

# Filter Data
df = df[df['seriesName'].isin(selected_series)]
if len(date_range) == 2:
    df = df[(df['date'] >= pd.Timestamp(date_range[0])) & (df['date'] <= pd.Timestamp(date_range[1]))]

# Visualization Section
st.title("Labor Statistics Dashboard")
st.subheader("Visualizations")

# Plot 1: Trends Over Time (Line Chart)
st.markdown("### 1. Trends Over Time")
fig_line = px.line(
    df,
    x="date",
    y="value",
    color="seriesName",
    title="Trends Over Time",
    labels={"value": "Value", "date": "Date", "seriesName": "Series"}
)
st.plotly_chart(fig_line)

# Plot 2: Proportions of Latest Data (Pie Chart)
st.markdown("### 2. Proportions of Latest Data")
latest_date = df['date'].max()
latest_data = df[df['date'] == latest_date]
fig_pie = px.pie(
    latest_data,
    names="seriesName",
    values="value",
    title=f"Proportions of Latest Data (Date: {latest_date})"
)
st.plotly_chart(fig_pie)

# Plot 3: Month-over-Month Change (Bar Chart)
st.markdown("### 3. Month-over-Month Percentage Change")
df['mom_change'] = df.groupby('seriesID')['value'].pct_change() * 100
fig_bar = px.bar(
    df,
    x="date",
    y="mom_change",
    color="seriesName",
    title="Month-over-Month Change",
    labels={"mom_change": "MoM Change (%)"}
)
st.plotly_chart(fig_bar)

# Plot 4: Rolling Averages
st.markdown("### 4. Rolling Averages")
rolling_window = st.slider("Rolling Window (Months)", 1, 12, 3)
df['rolling_mean'] = df.groupby('seriesName')['value'].transform(lambda x: x.rolling(rolling_window).mean())
fig_rolling = px.line(
    df,
    x="date",
    y="rolling_mean",
    color="seriesName",
    title=f"{rolling_window}-Month Rolling Averages",
    labels={"rolling_mean": "Rolling Average", "date": "Date", "seriesName": "Series"}
)
st.plotly_chart(fig_rolling)

# Plot 5: Correlation Heatmap
st.markdown("### 5. Correlation Heatmap")
corr_data = df.pivot(index="date", columns="seriesName", values="value")
corr_matrix = corr_data.corr()
fig_corr = px.imshow(
    corr_matrix,
    title="Correlation Matrix of Series",
    labels={"color": "Correlation"},
    color_continuous_scale="RdBu"
)
st.plotly_chart(fig_corr)

# Plot 6: Seasonal Trends
st.markdown("### 6. Seasonal Trends")
df['month'] = df['date'].dt.month
seasonal_data = df.groupby(['month', 'seriesName']).agg({'value': 'mean'}).reset_index()
fig_seasonal = px.line(
    seasonal_data,
    x="month",
    y="value",
    color="seriesName",
    title="Seasonal Trends",
    labels={"value": "Value", "month": "Month", "seriesName": "Series"}
)
st.plotly_chart(fig_seasonal)

# Plot 7: Value Distribution (Histogram)
st.markdown("### 7. Distribution of Values")
fig_histogram = px.histogram(
    df,
    x="value",
    color="seriesName",
    nbins=20,
    title="Distribution of Values",
    labels={"value": "Value", "seriesName": "Series"}
)
st.plotly_chart(fig_histogram)

# Plot 8: Cumulative Trends (Area Chart)
st.markdown("### 8. Cumulative Trends")
df['cumulative_value'] = df.groupby('seriesName')['value'].cumsum()
fig_cumulative = px.area(
    df,
    x="date",
    y="cumulative_value",
    color="seriesName",
    title="Cumulative Trends Over Time",
    labels={"cumulative_value": "Cumulative Value", "date": "Date", "seriesName": "Series"}
)
st.plotly_chart(fig_cumulative)

# Plot 9: Top and Bottom Performers
st.markdown("### 9. Top and Bottom Performers")
top_n = st.slider("Select Number of Top/Bottom Performers", 1, 10, 5)
top_data = latest_data.nlargest(top_n, 'value')
bottom_data = latest_data.nsmallest(top_n, 'value')
fig_top = px.bar(
    top_data,
    x="seriesName",
    y="value",
    color="seriesName",
    title="Top Performers",
    labels={"value": "Value", "seriesName": "Series"}
)
fig_bottom = px.bar(
    bottom_data,
    x="seriesName",
    y="value",
    color="seriesName",
    title="Bottom Performers",
    labels={"value": "Value", "seriesName": "Series"}
)
st.plotly_chart(fig_top)
st.plotly_chart(fig_bottom)

# Plot 10: Forecasting
st.markdown("### 10. Forecast Future Trends")
forecast_series = st.selectbox("Select a Series for Forecasting", df['seriesName'].unique())
forecast_data = df[df['seriesName'] == forecast_series].set_index('date')['value']
if len(forecast_data) > 12:  # Ensure sufficient data for forecasting
    model = ExponentialSmoothing(forecast_data, seasonal="add", seasonal_periods=12).fit()
    forecast = model.forecast(steps=12)
    fig_forecast = px.line(
        x=forecast.index.union(forecast_data.index),
        y=forecast_data.append(forecast),
        labels={"x": "Date", "y": "Value"},
        title=f"Forecast for {forecast_series}"
    )
    fig_forecast.add_scatter(x=forecast.index, y=forecast, mode='lines', name='Forecast')
    st.plotly_chart(fig_forecast)
else:
    st.warning("Not enough data to perform forecasting. Ensure at least one year of data is available.")

