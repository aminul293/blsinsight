import os
import requests
import pandas as pd
from datetime import datetime

# BLS API URL and API key
BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
API_KEY = "72bd5ec7070048a99f4892a5b9221399"

# Series IDs to fetch
series_ids = [
    "CEU0000000001",  # Total Non-Farm Workers
    "LNS14000000",    # Unemployment Rates
    "LNS11300000",    # Labor Force Participation Rate
    "CES0500000003",  # Average Hourly Earnings
    "CES9091000001",  # Construction Employment
    "LNS12000000",    # Employment-Population Ratio
]

# File to store the dataset
OUTPUT_FILE = "data/bls_cleaned_data.csv"


def load_existing_data(file_path):
    """Load existing data from a CSV file."""
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=["seriesID", "date", "value"])


def fetch_series_data(series_id, start_year):
    """Fetch data for a single series from the BLS API."""
    payload = {
        "seriesid": [series_id],
        "startyear": start_year,
        "endyear": str(datetime.now().year),
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


def fetch_and_update_data(output_file):
    """Fetch new data, append to existing data, and save."""
    existing_data = load_existing_data(output_file)

    # Determine the most recent date in the existing dataset
    if not existing_data.empty:
        last_date = pd.to_datetime(existing_data['date']).max()
        start_year = last_date.year
        start_month = last_date.month
    else:
        start_year = 2022
        start_month = 1

    all_data = []
    for series_id in series_ids:
        print(f"Fetching data for series: {series_id}")
        series_data = fetch_series_data(series_id, start_year)
        for item in series_data:
            date = f"{item['year']}-{item['period'][1:]}-01"
            if pd.to_datetime(date) > pd.to_datetime(f"{start_year}-{start_month:02d}-01"):
                all_data.append({
                    "seriesID": series_id,
                    "date": date,
                    "value": float(item['value'].replace(",", "")),
                })

    # Convert the new data to a DataFrame
    new_data = pd.DataFrame(all_data)
    new_data['date'] = pd.to_datetime(new_data['date'], errors='coerce')
    new_data = new_data.dropna(subset=['date'])

    # Combine new data with existing data
    combined_data = pd.concat([existing_data, new_data]).drop_duplicates()
    combined_data.sort_values(by="date", inplace=True)

    # Save updated data to CSV
    os.makedirs("data", exist_ok=True)
    combined_data.to_csv(output_file, index=False)
    print(f"Data updated and saved to {output_file}")


if __name__ == "__main__":
    fetch_and_update_data(OUTPUT_FILE)

