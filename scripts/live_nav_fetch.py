from pathlib import Path
import logging
import requests
import pandas as pd
import time

BASE_DIR = Path(__file__).resolve().parents[1]

LIVE_NAV_DIR = BASE_DIR / "data" / "raw" / "live_nav"
LIVE_NAV_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_DIR = BASE_DIR / "data" / "processed"

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "etl.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

FUND_MASTER = PROCESSED_DIR / "01_fund_master_clean.csv"
BASE_URL = "https://api.mfapi.in/mf/{}"
TIMEOUT = 30

def fetch_scheme(amfi_code, scheme_name):
    """Fetch NAV history for a single scheme and save to CSV."""
    try:
        response = requests.get(
            BASE_URL.format(amfi_code),
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        if "meta" not in data or "data" not in data:
            raise ValueError("Invalid API response")

        meta_df = pd.DataFrame([data["meta"]])
        nav_df = pd.DataFrame(data["data"])

        meta_df.to_csv(
            LIVE_NAV_DIR / f"{amfi_code}_meta.csv",
            index=False
        )

        nav_df.to_csv(
            LIVE_NAV_DIR / f"{amfi_code}_nav_history.csv",
            index=False
        )

        logger.info(f"{scheme_name} - Success")
        print(f"[SUCCESS] {scheme_name}")
    except Exception as e:
        logger.error(f"{scheme_name} - {e}")
        print(f"[FAILED] {scheme_name}")


def fetch_live_nav():
    """Fetch live NAV data for all configured schemes."""
    funds = pd.read_csv(FUND_MASTER)
    print(f"\nFound {len(funds)} schemes\n")

    for _, row in funds.iterrows():
        fetch_scheme(
            row["amfi_code"],
            row["scheme_name"]
        )
        time.sleep(0.5)

    print("\nCompleted fetching all schemes.")


if __name__ == "__main__":
    fetch_live_nav()