"""Theme helper to inject CSS."""
import streamlit as st
from pathlib import Path

def apply_theme() -> None:
    """Load and inject styles.css into Streamlit app."""
    css_path = Path(__file__).resolve().parent / "styles.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        st.warning("Styles stylesheet (styles.css) not found.")
