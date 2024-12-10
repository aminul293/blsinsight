import requests
import pandas as pd
import os
from datetime import datetime

# BLS API URL and API key
BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
API_KEY = "72bd5ec7070048a99f4892a5b9221399"  # Replace this with your actual BLS API key

# Series IDs to fetch
series_ids = [
    "CEU0000000001",  # Total Non-Farm Workers
    "LNS14000000",    # Unemployment Rates
    "LNS11300000",    # Labor Force Participation Rate
    "CES0500000003",  # Average Hourly Earnings
    "CES9091000001",  # Construction Employment
    "LNS12000000",    # Employment-Population Ratio
]


# Define date range
start_year = "2022"
end_year = str(datetime.now().year)

def fetch_series_data(series_id):
    """Fetch data for a single series from the BLS API."""
    payload = {
        "seriesid": [series_id],
        "startyear": start_year,
        "endyear": end_year,
        "registrationkey": API_KEY,
    }
    response = requests.post(BLS_API_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        if "Results" in data:
            return data["Results"]["series"][0]["data"]
        else:
            print(f"No data found for series: {series_id}")
            return []
    else:
        print(f"Error fetching data for series {series_id}: {response.status_code}")
        return []

def fetch_and_save_bls_data(output_file="data/bls_cleaned_data.csv"):
    """Fetch data for all series and save to a CSV file."""
    all_data = []
    for series_id in series_ids:
        print(f"Fetching data for series: {series_id}")
        series_data = fetch_series_data(series_id)
        for item in series_data:
            all_data.append({
                "seriesID": series_id,
                "date": f"{item['year']}-{item['period'][1:]}-01",  # Convert 'M01' to '01'
                "value": float(item['value'].replace(",", "")),
            })

    # Convert the data to a DataFrame
    df = pd.DataFrame(all_data)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])  # Remove invalid dates
    df.sort_values(by="date", inplace=True)

    # Save the data to a CSV file
    os.makedirs("data", exist_ok=True)
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    fetch_and_save_bls_data()
