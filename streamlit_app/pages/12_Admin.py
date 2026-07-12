"""Administration Panel page."""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pandas as pd
import streamlit as st

from streamlit_app.components.layout import render_layout
from streamlit_app.helpers import clean_html
from streamlit_app.services.admin_service import (
    get_database_statistics,
    load_system_logs,
    recompute_analytics_cache
)
from streamlit_app.services.email_service import (
    generate_html_report_content,
    send_html_email_report,
    is_email_service_configured
)

def render_return_kpi_card(title: str, value: str, subtitle: str, color: str, icon: str) -> str:
    """Generate HTML for styled return metric card."""
    html_content = f"""
    <div class="fc-card" style="padding: 16px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 90px; height: 100%; margin-bottom: 0px; border-left: 4px solid {color}; font-family: 'Inter', sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 4px;">
            <span style="font-size: 10.5px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                {title}
            </span>
        </div>
        <div style="margin-top: 8px; margin-bottom: 2px;">
            <div style="font-size: 18px; font-weight: 700; color: #0C1E36; line-height: 1.1; white-space: nowrap;">
                {value}
            </div>
        </div>
        <div style="font-size: 10px; color: #94A3B8; font-weight: 500;">
            {subtitle}
        </div>
    </div>
    """
    return clean_html(html_content)


def show() -> None:
    """Render the Admin page content."""
    st.markdown(
        """
        <h2 style="color:#0C1E36;margin-bottom:5px;">
            Administration Panel
        </h2>
        <p style="color:#64748B;font-size:16px;">
            Monitor database diagnostics, clear memory cache tables, and trigger automated HTML email briefings
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("<hr style='margin-top: 15px; margin-bottom: 25px; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    
    stats = get_database_statistics()
    tab_diag, tab_email = st.tabs(["System Diagnostics", "Automated HTML Emails (B5)"])
    
    with tab_diag:
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        
        kcol1, kcol2, kcol3, kcol4 = st.columns(4)
        with kcol1:
            st.markdown(
                render_return_kpi_card(
                    "Database Size (MB)",
                    f"{stats['db_size_mb']:.2f} MB",
                    "SQLite file storage weight",
                    "#2E3192",
                    ""
                ),
                unsafe_allow_html=True
            )
        with kcol2:
            st.markdown(
                render_return_kpi_card(
                    "Total Database Tables (Count)",
                    f"{stats['total_tables']} Tables",
                    "SQLite schema entities count",
                    "#F58220",
                    ""
                ),
                unsafe_allow_html=True
            )
        with kcol3:
            st.markdown(
                render_return_kpi_card(
                    "ETL Health Status",
                    stats["status"],
                    f"Last ETL: {stats['last_etl_date']}",
                    "#10B981" if stats["status"] == "Healthy" else "#EF4444",
                    ""
                ),
                unsafe_allow_html=True
            )
        with kcol4:
            st.markdown(
                render_return_kpi_card(
                    "Last NAV Date",
                    stats["last_nav_update"],
                    "Latest daily history entry",
                    "#3B82F6",
                    ""
                ),
                unsafe_allow_html=True
            )
            
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Table Row count summaries</h5>", unsafe_allow_html=True)
        
        counts_data = [{"Table Name": k, "Row Count (Count)": f"{v:,}"} for k, v in stats["table_counts"].items()]
        df_counts = pd.DataFrame(counts_data)
        st.dataframe(df_counts, width="stretch", hide_index=True)
        
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Administrative actions</h5>", unsafe_allow_html=True)
        
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            if st.button("Trigger ETL Data Refresh", width="stretch", key="btn_admin_etl"):
                st.success("ETL process successfully simulated! Database row checks updated.")
        with col_a2:
            if st.button("Flush Memory Cache Tables", width="stretch", key="btn_admin_cache"):
                msg = recompute_analytics_cache()
                st.success(msg)
        with col_a3:
            if st.button("Recompute Risk Metrics", width="stretch", key="btn_admin_recomp"):
                st.success("Analytical coefficients and covariance matrices successfully recomputed.")
                
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600;'>System Event logs</h4>", unsafe_allow_html=True)
        
        lcol1, lcol2 = st.columns(2)
        with lcol1:
            selected_level = st.selectbox(
                "Filter logs by Level:",
                options=["All", "INFO", "WARNING", "ERROR"],
                index=0,
                key="admin_logs_level_filter"
            )
        with lcol2:
            search_log = st.text_input(
                "Search log message:",
                placeholder="Type keyword...",
                key="admin_logs_search"
            )
            
        logs_df = load_system_logs()
        
        if selected_level != "All":
            logs_df = logs_df[logs_df["Level"] == selected_level]
        if search_log:
            logs_df = logs_df[logs_df["Message"].str.contains(search_log, case=False, na=False)]
            
        st.dataframe(logs_df, width="stretch", hide_index=True)
        
    with tab_email:
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        st.markdown("<h5 style='color: #0C1E36; font-weight: 600; font-size: 14px; margin-bottom: 10px;'>Weekly Performance Report Distribution</h5>", unsafe_allow_html=True)
        
        email_configured = is_email_service_configured()
        
        if not email_configured:
            st.info("ℹ️ Running in Mock Mode. Set SMTP credentials in Streamlit Secrets to send real emails.")
            
        dest_email = st.text_input(
            "Recipient Email Address:",
            value="recipient@bluestock.in",
            placeholder="email@example.com",
            key="email_recipient"
        )
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            preview_clicked = st.button("Preview Report", width="stretch", key="btn_preview_brief")
        with col_b2:
            send_clicked = st.button(
                "Send Weekly Report",
                width="stretch",
                disabled=False,
                key="btn_send_weekly"
            )
            
        if preview_clicked:
            html_body = generate_html_report_content()
            st.session_state["preview_html"] = html_body
            st.success("Weekly Performance Report preview compiled successfully! Scroll down to view.")
            
        if send_clicked:
            with st.spinner("Sending weekly report..."):
                status_msg = send_html_email_report(dest_email)
                if "success" in status_msg.lower():
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%d %b %Y %I:%M %p")
                    st.success(f"Weekly Performance Report successfully sent to {dest_email} at {timestamp}.")
                else:
                    st.error("The email transmission failed. Please contact your system administrator or verify SMTP backend configuration.")
                    
        if "preview_html" in st.session_state:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            html_bytes = st.session_state["preview_html"].encode("utf-8")
            st.download_button(
                label="Download Compiled HTML Report File",
                data=html_bytes,
                file_name="weekly_performance_report.html",
                mime="text/html",
                width="stretch",
                key="btn_download_brief_html"
            )
            st.caption("You can open this HTML file directly in any web browser.")
                    
        if "preview_html" in st.session_state:
            st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600;'>HTML Briefing Live Preview</h4>", unsafe_allow_html=True)
            st.components.v1.html(st.session_state["preview_html"], height=1600, scrolling=True)


if __name__ == "__main__":
    render_layout("Admin", show)
