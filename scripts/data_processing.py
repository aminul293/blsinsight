import pandas as pd

def process_data(input_file="data/bls_data.csv", output_file="data/bls_cleaned_data.csv"):
    df = pd.read_csv(input_file)
    df['date'] = pd.to_datetime(df['year'].astype(str) + df['periodName'], format='%Y%B')
    df = df[['date', 'seriesID', 'value']]
    df.to_csv(output_file, index=False)

if __name__ == "__main__":
    process_data()
