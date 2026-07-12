from live_nav_fetch import fetch_live_nav
from clean_daily_nav import clean_daily_nav
from update_database import update_dim_date, update_database, update_etl_metadata


def run_pipeline():

    print("=" * 60)
    print("Starting Daily ETL Pipeline")
    print("=" * 60)

    fetch_live_nav()

    clean_daily_nav()

    update_dim_date()

    update_database()

    update_etl_metadata()

    print("\nETL Completed Successfully")


if __name__ == "__main__":
    run_pipeline()