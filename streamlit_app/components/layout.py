"""Layout template."""
import streamlit as st
from typing import Callable
from streamlit_app.theme import apply_theme
from streamlit_app.components.navbar import render_navbar
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.footer import render_footer

def render_layout(page_title: str, content_func: Callable[[], None]) -> None:
    """Render layout structure with sidebar, navbar, content, footer."""
    apply_theme()
    render_sidebar(page_title)
    render_navbar(page_title)
    
    content_container = st.container()
    with content_container:
        content_func()
        
    render_footer()
