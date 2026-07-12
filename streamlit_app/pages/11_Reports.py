"""Reports and Export page."""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pandas as pd
import streamlit as st

from streamlit_app.components.layout import render_layout
from streamlit_app.helpers import clean_html
from streamlit_app.services.report_service import (
    get_dataset_choices,
    fetch_report_dataframe,
    export_to_csv,
    export_to_excel,
    export_to_pdf,
)

def show() -> None:
    """Render the Reports and Export page."""
    st.markdown(
        """
        <h2 style="color:#0C1E36;margin-bottom:5px;">
            Reports & Export
        </h2>
        <p style="color:#64748B;font-size:16px;">
            Download custom tabular CSV datasheets, styled Excel sheets, and executive PDF briefing reports
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("<hr style='margin-top: 15px; margin-bottom: 25px; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    
    dataset_choices = get_dataset_choices()
    
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_dataset = st.selectbox(
            "Choose Report Dataset to Export:",
            options=dataset_choices,
            index=0,
            key="export_dataset_select"
        )
    with col_sel2:
        st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
        
    df = fetch_report_dataframe(selected_dataset)
    
    if df.empty:
        st.info("No records are available for the selected dataset.")
        return
        
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        search_query = st.text_input(
            "Search in report data:",
            placeholder="Type keywords (e.g. Nippon, Equity, Karnataka)...",
            key="reports_search_query"
        )
    with fcol2:
        cat_col = None
        for col in ["Category", "State", "Sector"]:
            if col in df.columns:
                cat_col = col
                break
        
        selected_cat = "All"
        if cat_col:
            unique_cats = ["All"] + sorted(df[cat_col].dropna().unique().tolist())
            selected_cat = st.selectbox(
                f"Filter by {cat_col}:",
                options=unique_cats,
                index=0,
                key=f"reports_cat_filter_{cat_col}"
            )
            
    if selected_cat != "All" and cat_col:
        df = df[df[cat_col] == selected_cat]
        
    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df = df[mask]
        
    st.markdown(
        f"""
        <div style="margin-top: 20px; margin-bottom: 10px;">
            <span style="font-weight: 700; color: #2E3192; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">
                Previewing top 10 of {len(df):,} matching records
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.dataframe(df.head(10), width="stretch", hide_index=True)
    
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Generate and Download files</h5>", unsafe_allow_html=True)
    
    clean_name = selected_dataset.lower().replace(" ", "_").replace("&", "and")
    
    dcol1, dcol2, dcol3 = st.columns(3)
    
    with dcol1:
        csv_bytes = export_to_csv(df)
        st.download_button(
            label="Download CSV Sheet",
            data=csv_bytes,
            file_name=f"{clean_name}.csv",
            mime="text/csv",
            key="btn_download_csv"
        )
        st.caption("Standard comma-separated value format.")
        
    with dcol2:
        xlsx_bytes = export_to_excel(df)
        st.download_button(
            label="Download Excel Spreadsheet",
            data=xlsx_bytes,
            file_name=f"{clean_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_download_excel"
        )
        st.caption("Excel file with sheet tabs.")
        
    with dcol3:
        pdf_bytes = export_to_pdf(df, selected_dataset)
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=f"{clean_name}.pdf",
            mime="application/pdf",
            key="btn_download_pdf"
        )
        st.caption("Branded executive PDF briefing (top 100 rows).")
        
    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
    st.markdown(
        clean_html("""
        <div class="fc-card" style="padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <h5 style="color: #2E3192; font-weight: 700; margin-top: 0; font-size: 13px; text-transform: uppercase;">ℹ️ Export & reporting specifications</h5>
            <p style="color: #475569; font-size: 13px; line-height: 1.5; margin-bottom: 0;">
                All reports are generated directly from the platform's active SQLite database. Excel sheets are created using the openpyxl writer engine, and PDF documents are compiled using a structured, branded layout template that matches the BlueStock corporate themes. To ensure prompt downloads, PDFs are capped to the top 100 records of the selected query.
            </p>
        </div>
        """),
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    render_layout("Reports", show)
