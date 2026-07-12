"""Configuration settings."""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"

# Colors
COLOR_PRIMARY = "#2E3192"      # Blue
COLOR_ACCENT = "#F58220"       # Orange
COLOR_BACKGROUND = "#F5F7FB"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT = "#0C1E36"

# App Info
APP_TITLE = "BlueStock Mutual Fund Analytics"
APP_SUBTITLE = "Analytics Platform"
APP_VERSION = "1.0.0"

