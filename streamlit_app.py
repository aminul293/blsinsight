 st.stop()
except ValueError as e:
    st.error(str(e))
    st.stop()

# Map series IDs to human-readable names
series_descriptions = {
    "CEU0000000001": "To    "CES0500000003": "Average Hourly Earnings",
    "LNS12000000": "Employment Population Ratio",
    "CES3000000001": "Total Manufacturing Employment",
    "CES9091000001": "Construction Employment",
    "LNS13000000": "Employment Level",
    "CES9092000001": "Transportation Employment",
    "LNS13327709": "Self-Employed Workers"
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Visualizations", "Raw Data", "Summary Insights", "Correlation>


