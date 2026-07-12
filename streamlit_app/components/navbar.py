import streamlit as st
import datetime
from streamlit_app.database import check_db_status, get_last_etl_date
from streamlit_app.helpers import clean_html

def render_navbar(page_title: str) -> None:
    """Render top navigation bar."""
    db_connected = check_db_status()
    db_status_text = "Active" if db_connected else "Disconnected"
    db_status_color = "#28a745" if db_connected else "#dc3545"
    
    last_etl = get_last_etl_date() or "Unknown"
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(
            clean_html(f"""
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="background-color: #2E3192; color: white; padding: 6px 12px; border-radius: 6px; font-weight: 800; font-size: 16px; font-family: 'Inter', sans-serif;">
                    BS
                </div>
                <div style="font-size: 20px; font-weight: 700; color: #0C1E36; font-family: 'Inter', sans-serif;">
                    {page_title}
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )
        
    with col2:
        st.markdown(
            clean_html(f"""
            <div style="display: flex; justify-content: flex-end; align-items: center; gap: 15px; font-size: 12px; font-family: 'Inter', sans-serif; height: 100%;">
                <div style="background: white; padding: 6px 12px; border-radius: 6px; border: 1px solid #E2E8F0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); display: flex; align-items: center;">
                    <span style="color: #64748B; font-weight: 500;">DB Status:</span>
                    <span style="color: {db_status_color}; font-weight: 600; margin-left: 5px; display: inline-flex; align-items: center; gap: 4px;">
                        <span style="width: 6px; height: 6px; border-radius: 50%; background-color: {db_status_color}; display: inline-block;"></span>
                        {db_status_text}
                    </span>
                </div>
                <div style="background: white; padding: 6px 12px; border-radius: 6px; border: 1px solid #E2E8F0; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <span style="color: #64748B; font-weight: 500;">Last ETL:</span>
                    <span style="color: #0C1E36; font-weight: 600; margin-left: 5px;">{last_etl}</span>
                </div>
                <div style="background: white; padding: 6px 12px; border-radius: 6px; border: 1px solid #E2E8F0; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <span style="color: #64748B; font-weight: 500;">Date:</span>
                    <span style="color: #0C1E36; font-weight: 600; margin-left: 5px;">{current_date}</span>
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )
    
    st.markdown("<hr style='margin-top: 12px; margin-bottom: 25px; border-color: #E2E8F0; border-width: 1px;'>", unsafe_allow_html=True)
