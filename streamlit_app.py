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

    # Distribution Analysis
    st.subheader("Distribution Analysis (Box Plot)")
    fig_box = px.box(
        df, x="seriesName", y="value",
        title="Box Plot of Series Values",
        labels={"value": "Value", "seriesName": "Series"}
    )
    st.plotly_chart(fig_box)

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

    # Proportions (Pie Chart)
    st.subheader("Proportions of Latest Data (Pie Chart)")
    latest_date = df['date'].max()
    latest_data = df[df['date'] == latest_date]
    fig_pie = px.pie(
        latest_data, names="seriesName", values="value",
        title=f"Proportions of Latest Data (Date: {latest_date.date()})"
    )
    st.plotly_chart(fig_pie)

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

    st.subheader("Scatter Plot with Regression Line")
    x_series = st.selectbox("Select X-Axis Series", options=df['seriesName'].unique())
    y_series = st.selectbox("Select Y-Axis Series", options=df['seriesName'].unique(), index=1)

    scatter_data = df[df['seriesName'].isin([x_series, y_series])]
    scatter_pivot = scatter_data.pivot(index='date', columns='seriesName', values='value')

    if len(scatter_pivot.dropna()) > 1:
        fig_scatter = px.scatter(
            scatter_pivot, x=x_series, y=y_series, trendline="ols",
            title=f"Scatter Plot of {x_series} vs {y_series}"
        )
        st.plotly_chart(fig_scatter)

# Tab 5: Forecasting
with tab5:
    st.subheader("Forecast Future Trends")
    forecast_series = st.selectbox("Select a Series for Forecasting", options=df['seriesName'].unique())

    # Filter data for the selected series
    forecast_df = df[df['seriesName'] == forecast_series].copy()
    forecast_df.set_index('date', inplace=True)

    if len(forecast_df) > 12:
        model = ExponentialSmoothing(
            forecast_df['value'], trend="additive", seasonal="additive", seasonal_periods=12
        )
        fitted_model = model.fit()
        forecast = fitted_model.forecast(12)  # Forecast the next 12 months

        # Plot forecast
        fig_forecast = px.line(forecast_df, y='value', x=forecast_df.index, title="Forecasting Future Trends")
        fig_forecast.add_scatter(x=forecast.index, y=forecast, mode='lines', name='Forecast')
        st.plotly_chart(fig_forecast)
    else:
        st.info("Not enough data points for forecasting (minimum 12 months required).")
