import pandas as pd
import os

csv_path = os.path.join(os.path.dirname(__file__), "swiss_major_cities.csv")

try:
    df = pd.read_csv(csv_path)
except Exception as e:
    print(f"Error loading cities CSV: {e}")
    df = pd.DataFrame(columns=["city", "lat", "lng"])

CITIES = {
    row["city"]: {"lat": float(row["lat"]), "lng": float(row["lng"])}
    for _, row in df.iterrows()
    if pd.notna(row["city"]) and pd.notna(row["lat"]) and pd.notna(row["lng"])
}