"""App entry point."""
import sys
from pathlib import Path
import streamlit as st

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

st.set_page_config(
    page_title="BlueStock Mutual Fund Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

import streamlit_app.constants as constants

# Navigation setup
pages = []
for page_name in constants.PAGES_LIST:
    file_path = constants.PAGE_FILES[page_name]
    is_default = (page_name == "Dashboard")
    pages.append(st.Page(file_path, title=page_name, default=is_default))

pg = st.navigation(pages, position="hidden")
pg.run()

