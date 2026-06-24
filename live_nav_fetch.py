import requests
import pandas as pd
import os

os.makedirs("data/raw", exist_ok=True)

scheme_code = "125497"

url = f"https://api.mfapi.in/mf/{scheme_code}"

response = requests.get(url)

data = response.json()

# META DATA
meta_df = pd.DataFrame([data["meta"]])

meta_df.to_csv(
    f"data/raw/{scheme_code}_meta.csv",
    index=False
)

# NAV HISTORY
nav_df = pd.DataFrame(data["data"])

nav_df.to_csv(
    f"data/raw/{scheme_code}_nav_history.csv",
    index=False
)

print("\nMeta Shape")
print(meta_df.shape)

print("\nNAV Shape")
print(nav_df.shape)

print("\nMeta Preview")
print(meta_df.head())

print("\nNAV Preview")
print(nav_df.head())

print("\nFiles Saved Successfully")