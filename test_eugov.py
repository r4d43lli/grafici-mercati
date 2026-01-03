import requests
import pandas as pd

# Example: Retrieve GDP per capita (dataset: nama_10_pc) for EU27 in 2022
# API documentation: https://ec.europa.eu/eurostat/web/json-and-unicode-web-services/getting-started/rest-request
url = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "nama_10_pc?geo=EU27_2020&time=2023"
)

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # Raise error for HTTP issues
    data = response.json()

    # Convert JSON to DataFrame
    df = pd.DataFrame(data['value'].items(), columns=['Index', 'Value'])
    print(df.head())

except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
