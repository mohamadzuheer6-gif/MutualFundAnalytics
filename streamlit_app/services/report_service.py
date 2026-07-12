"""Report generation and export service."""
from __future__ import annotations
import io
import sqlite3
import pandas as pd
from fpdf import FPDF

from streamlit_app.config import DB_PATH
from streamlit_app.database import get_db_connection

class PDFReport(FPDF):
    """Custom FPDF layout for BlueStock reports."""
    def header(self):
        self.set_font('helvetica', 'B', 14)
        self.set_text_color(46, 49, 146)
        self.cell(0, 8, 'BlueStock Mutual Fund Analytics Platform', border=False, ln=1, align='L')
        
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, 'Executive Financial Summary Report', border=False, ln=1, align='L')
        self.ln(6)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')


def export_to_csv(df: pd.DataFrame) -> bytes:
    """Export DataFrame to UTF-8 CSV bytes."""
    return df.to_csv(index=False).encode('utf-8')


def export_to_excel(df: pd.DataFrame) -> bytes:
    """Export DataFrame to Excel (.xlsx) bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Data_Export")
    return output.getvalue()


def export_to_pdf(df: pd.DataFrame, title: str) -> bytes:
    """Export DataFrame to a styled PDF."""
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(12, 30, 54)
    pdf.cell(0, 8, f"Dataset Summary: {title}".replace("₹", "Rs."), ln=1)
    
    pdf.set_font("helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, f"Showing top {min(len(df), 100)} records of {len(df)} total rows.", ln=1)
    pdf.ln(4)
    
    if df.empty:
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 10, "No records found.", ln=1)
        return bytes(pdf.output())
        
    num_cols = len(df.columns)
    page_width = 190.0
    col_width = page_width / num_cols
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(46, 49, 146)
    pdf.set_text_color(255, 255, 255)
    
    for col in df.columns:
        col_title = str(col).replace("₹", "Rs.")
        if len(col_title) > 15:
            col_title = col_title[:12] + ".."
        pdf.cell(col_width, 7, col_title, border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(50, 50, 50)
    
    for idx, row in df.head(100).iterrows():
        fill_row = (idx % 2 == 1)
        if fill_row:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(255, 255, 255)
            
        for col in df.columns:
            val = str(row[col]).replace("₹", "Rs.")
            if len(val) > 22:
                val = val[:19] + "..."
            pdf.cell(col_width, 6, val, border=1, fill=fill_row)
        pdf.ln()
        
    return bytes(pdf.output())


def get_dataset_choices() -> list[str]:
    """Get choices of exportable datasets."""
    return [
        "NAV Analytics History",
        "Fund Risk Statistics",
        "Investor Behavior & Transactions",
        "Portfolio stock holdings"
    ]


def fetch_report_dataframe(dataset_name: str) -> pd.DataFrame:
    """Fetch report data from SQLite."""
    conn = get_db_connection()
    
    if dataset_name == "NAV Analytics History":
        query = """
        SELECT 
            f.scheme_name AS [Scheme Name],
            f.category AS [Category],
            d.full_date AS [Date],
            n.nav AS [NAV (₹)]
        FROM fact_nav n
        JOIN dim_fund f ON n.fund_id = f.fund_id
        JOIN dim_date d ON n.date_id = d.date_id
        ORDER BY d.full_date DESC
        LIMIT 1000
        """
        df = pd.read_sql_query(query, conn)
        
    elif dataset_name == "Fund Risk Statistics":
        query = """
        SELECT 
            f.scheme_name AS [Scheme Name],
            f.category AS [Category],
            r.sharpe_ratio AS [Sharpe Ratio],
            r.std_dev_ann_pct AS [Annualized Volatility (%)],
            r.alpha AS [Alpha (%)],
            r.beta AS [Beta],
            r.sortino_ratio AS [Sortino Ratio]
        FROM fact_performance r
        JOIN dim_fund f ON r.fund_id = f.fund_id
        ORDER BY r.sharpe_ratio DESC
        """
        df = pd.read_sql_query(query, conn)
        
    elif dataset_name == "Investor Behavior & Transactions":
        query = """
        SELECT 
            t.transaction_id AS [Tx ID],
            t.transaction_type AS [Type],
            t.amount_inr AS [Transaction Amount (₹)],
            t.state AS [State],
            t.city_tier AS [City Tier],
            t.age_group AS [Age Group]
        FROM fact_transactions t
        ORDER BY t.transaction_id DESC
        LIMIT 1000
        """
        df = pd.read_sql_query(query, conn)
        
    elif dataset_name == "Portfolio stock holdings":
        query = """
        SELECT 
            f.scheme_name AS [Fund Name],
            h.stock_name AS [Stock],
            h.sector AS [Sector],
            h.weight_pct AS [Weight (%)],
            h.market_value_cr AS [Market Value (₹ Crore)]
        FROM stg_portfolio_holdings h
        JOIN dim_fund f ON h.amfi_code = f.amfi_code
        ORDER BY h.weight_pct DESC
        """
        df = pd.read_sql_query(query, conn)
        
    else:
        df = pd.DataFrame()
        
    conn.close()
    return df
