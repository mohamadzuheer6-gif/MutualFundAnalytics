import streamlit as st

def render_footer() -> None:
    """Render footer."""
    st.markdown(
        """
        <div style="margin-top: 80px; padding: 25px 0; border-top: 1px solid #E2E8F0; text-align: center; color: #64748B; font-size: 12px; font-family: 'Inter', sans-serif;">
            <p style="margin: 0; font-weight: 500;">
                © 2026 BlueStock Mutual Fund Analytics Platform. All rights reserved.
            </p>
            <p style="margin: 6px 0 0 0; color: #94A3B8;">
                BlueStock Data Analyst Internship Project
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
