import requests
import pandas as pd
import json

API_KEY = "72bd5ec7070048a99f4892a5b9221399"  # Replace with your actual BLS API key
BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
SERIES_IDS = [
    "CEU0000000001",  # Total Non-Farm Workers
    "LNS14000000",    # Unemployment Rates
    "LNS11300000"     # Labor Force Participation Rate
]

def fetch_bls_data(series_ids, start_year, end_year):
    headers = {'Content-type': 'application/json'}
    data = json.dumps({
        "seriesid": series_ids,
        "startyear": start_year,
        "endyear": end_year,
        "registrationkey": API_KEY
    })
    response = requests.post(BASE_URL, headers=headers, data=data)
    return response.json()

def save_data(json_data, output_file="data/bls_data.csv"):
    all_series = []
    for series in json_data['Results']['series']:
        series_id = series['seriesID']
        series_data = series['data']
        df = pd.DataFrame(series_data)
        df['seriesID'] = series_id
        all_series.append(df)

    final_df = pd.concat(all_series)
    final_df.to_csv(output_file, index=False)

if __name__ == "__main__":
    data = fetch_bls_data(SERIES_IDS, start_year="2022", end_year="2024")
    save_data(data)
