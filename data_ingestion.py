import pandas as pd
import os

DATA_FOLDER = "data/raw"

files = sorted(
    [f for f in os.listdir(DATA_FOLDER)
     if f.endswith(".csv")]
)

print(f"\nTotal files found: {len(files)}\n")

for file in files:

    print("\n" + "="*80)
    print(f"FILE: {file}")
    print("="*80)

    path = os.path.join(DATA_FOLDER, file)

    df = pd.read_csv(path)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nData Types:")
    print(df.dtypes)

    print("\nFirst 5 Rows:")
    print(df.head())

    print("\nMissing Values:")
    print(df.isnull().sum())