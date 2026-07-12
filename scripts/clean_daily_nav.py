from pathlib import Path
import pandas as pd
import logging

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = BASE_DIR / "data" / "raw" / "live_nav"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = BASE_DIR / "logs" / "etl.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def clean_daily_nav():

    nav_files = sorted(RAW_DIR.glob("*_nav_history.csv"))

    if not nav_files:
        raise FileNotFoundError("No NAV history files found.")

    all_data = []

    for file in nav_files:

        amfi_code = file.stem.split("_")[0]

        try:
            df = pd.read_csv(file)

            if df.empty:
                print(f"Skipping empty file: {file.name}")
                logger.warning(f"Empty file skipped: {file.name}")
                continue

            df["amfi_code"] = amfi_code

            all_data.append(df)

        except pd.errors.EmptyDataError:
            print(f"Corrupted/empty CSV: {file.name}")
            logger.warning(f"Corrupted CSV skipped: {file.name}")
            continue

    nav_df = pd.concat(all_data, ignore_index=True)

    nav_df["date"] = pd.to_datetime(
        nav_df["date"],
        format="%d-%m-%Y",
        errors="coerce"
    )

    nav_df["nav"] = pd.to_numeric(
        nav_df["nav"],
        errors="coerce"
    )

    nav_df = nav_df.dropna(subset=["date", "nav"])

    nav_df = nav_df[nav_df["nav"] > 0]

    nav_df = nav_df.sort_values(
        ["amfi_code", "date"]
    )

    nav_df = nav_df.drop_duplicates(
        subset=["amfi_code", "date"]
    )

    output_file = PROCESSED_DIR / "daily_nav_clean.csv"

    nav_df.to_csv(output_file, index=False)

    logger.info(
        f"Daily NAV cleaned successfully. Rows: {len(nav_df)}"
    )

    print(f"\nRows : {len(nav_df)}")

    print(f"Saved : {output_file}")


if __name__ == "__main__":

    clean_daily_nav()