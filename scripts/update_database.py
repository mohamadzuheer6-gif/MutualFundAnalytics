from pathlib import Path
import logging

import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
NAV_FILE = PROCESSED_DIR / "daily_nav_clean.csv"
LOG_FILE = BASE_DIR / "logs" / "etl.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)
engine = create_engine(f"sqlite:///{DB_PATH}")

print("Connected Successfully")
logger.info("Connected to SQLite database")


def update_dim_date():
    """Insert missing dates into the date dimension table."""
    nav_df = pd.read_csv(NAV_FILE)
    nav_df["date"] = pd.to_datetime(nav_df["date"])
    csv_dates = set(nav_df["date"].dt.normalize())

    dim_date = pd.read_sql(
        "SELECT full_date FROM dim_date",
        engine
    )
    dim_date["full_date"] = pd.to_datetime(dim_date["full_date"])
    db_dates = set(dim_date["full_date"].dt.normalize())

    missing_dates = sorted(csv_dates - db_dates)
    if not missing_dates:
        print("No new dates found.")
        logger.info("dim_date already up to date")
        return

    new_dates = pd.DataFrame({"full_date": missing_dates})
    new_dates["year"] = new_dates["full_date"].dt.year
    new_dates["quarter"] = new_dates["full_date"].dt.quarter
    new_dates["month"] = new_dates["full_date"].dt.month
    new_dates["month_name"] = new_dates["full_date"].dt.month_name()
    new_dates["day"] = new_dates["full_date"].dt.day
    new_dates["weekday"] = new_dates["full_date"].dt.day_name()

    new_dates.to_sql(
        "dim_date",
        engine,
        if_exists="append",
        index=False
    )
    print(f"Inserted {len(new_dates)} new dates.")
    logger.info(f"{len(new_dates)} new dates added to dim_date")


def update_database():
    """Load new NAV records into fact_nav."""
    print("\nUpdating fact_nav...")
    logger.info("Updating fact_nav")

    nav_df = pd.read_csv(NAV_FILE)
    nav_df["date"] = pd.to_datetime(nav_df["date"])

    fund_lookup = pd.read_sql(
        "SELECT fund_id, amfi_code FROM dim_fund",
        engine
    )

    date_lookup = pd.read_sql(
        "SELECT date_id, full_date FROM dim_date",
        engine
    )
    date_lookup["full_date"] = pd.to_datetime(date_lookup["full_date"])

    nav_df = nav_df.merge(fund_lookup, on="amfi_code", how="left")
    nav_df = nav_df.merge(date_lookup, left_on="date", right_on="full_date", how="left")

    print("Fund mapping completed.")
    print("Date mapping completed.")

    nav_df = nav_df[["fund_id", "date_id", "nav"]]

    existing_nav = pd.read_sql(
        "SELECT fund_id, date_id FROM fact_nav",
        engine
    )

    new_nav = nav_df.merge(
        existing_nav,
        on=["fund_id", "date_id"],
        how="left",
        indicator=True
    )
    new_nav = new_nav[new_nav["_merge"] == "left_only"].drop(columns="_merge")

    print(f"New NAV rows : {len(new_nav)}")
    logger.info(f"New NAV rows : {len(new_nav)}")

    if len(new_nav) > 0:
        new_nav.to_sql(
            "fact_nav",
            engine,
            if_exists="append",
            index=False
        )
        print("Database updated successfully.")
        logger.info("fact_nav updated successfully.")
    else:
        print("Database already up to date.")
        logger.info("No new NAV records.")


def update_etl_metadata():
    """Update the last successful ETL run timestamp."""
    print("\nUpdating ETL metadata...")
    logger.info("Updating ETL metadata")
    import datetime
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS etl_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """))
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                text("INSERT OR REPLACE INTO etl_metadata (key, value) VALUES (:key, :value)"),
                {"key": "last_etl_run", "value": current_time}
            )
            print(f"ETL metadata updated: last_etl_run = {current_time}")
            logger.info(f"ETL metadata updated: last_etl_run = {current_time}")
    except Exception as e:
        print(f"Failed to update ETL metadata: {e}")
        logger.error(f"Failed to update ETL metadata: {e}")


if __name__ == "__main__":
    update_dim_date()
    update_database()
    update_etl_metadata()