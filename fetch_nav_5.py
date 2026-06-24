import requests
import pandas as pd
import os

os.makedirs("data/raw", exist_ok=True)

schemes = {
    "SBI_Bluechip": "119551",
    "ICICI_Bluechip": "120503",
    "Nippon_Large_Cap": "118632",
    "Axis_Bluechip": "119092",
    "Kotak_Bluechip": "120841"
}

for fund_name, code in schemes.items():

    print(f"\nProcessing {fund_name}")

    url = f"https://api.mfapi.in/mf/{code}"

    data = requests.get(url).json()

    meta_df = pd.DataFrame([data["meta"]])

    nav_df = pd.DataFrame(data["data"])

    meta_df.to_csv(
        f"data/raw/{fund_name}_meta.csv",
        index=False
    )

    nav_df.to_csv(
        f"data/raw/{fund_name}_nav_history.csv",
        index=False
    )

    print("Saved")