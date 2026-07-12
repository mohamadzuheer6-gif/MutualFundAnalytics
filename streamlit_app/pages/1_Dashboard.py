"""Dashboard page for Mutual Fund Analytics."""
import sys
from pathlib import Path
import datetime
import os
import sqlite3
from typing import Dict, Any, List

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from streamlit_app.components.layout import render_layout
from streamlit_app.database import check_db_status, get_last_etl_date
from streamlit_app.config import DB_PATH
from streamlit_app.helpers import clean_html

@st.cache_data
def load_aum_data() -> pd.DataFrame:
    """Load Industry AUM data from SQLite."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    query = """
        SELECT a.aum_id, a.date_id, a.fund_house, a.aum_lakh_crore, a.aum_crore, a.num_schemes,
               d.full_date, d.year
        FROM fact_aum a
        JOIN dim_date d ON a.date_id = d.date_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['full_date'] = pd.to_datetime(df['full_date'])
    return df


@st.cache_data
def load_sip_inflows() -> pd.DataFrame:
    """Load monthly SIP inflows."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM stg_monthly_sip_inflows", conn)
    conn.close()
    df['month'] = pd.to_datetime(df['month'])
    return df


@st.cache_data
def load_folios_data() -> pd.DataFrame:
    """Load folio counts."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM stg_industry_folio_count", conn)
    conn.close()
    df['month'] = pd.to_datetime(df['month'])
    return df


@st.cache_data
def load_portfolio_data() -> pd.DataFrame:
    """Load selected funds data."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    query = """
        SELECT f.fund_id, f.fund_house, f.scheme_name, f.category, f.sub_category, f.plan, f.risk_category,
               p.aum_crore
        FROM dim_fund f
        JOIN fact_performance p ON f.fund_id = p.fund_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def render_status_bar() -> str:
    """Render Platform Status bar."""
    db_connected = check_db_status()
    db_status_text = "Connected" if db_connected else "Disconnected"
    db_status_color = "#28a745" if db_connected else "#dc3545"
    
    last_etl = get_last_etl_date() or "Unknown"
    
    return f"""
    <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; width: 100%;">
        <div style="display: flex; align-items: center; gap: 8px; font-family: 'Inter', sans-serif;">
            <span style="font-size: 16px; line-height: 1;"></span>
            <span style="font-weight: 700; color: #2E3192; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">Platform Status</span>
        </div>
        <div style="display: flex; gap: 30px; align-items: center; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 8px; font-family: 'Inter', sans-serif; font-size: 13px; white-space: nowrap;">
                <span style="color: #64748B; font-weight: 500;">Database Connection:</span>
                <span style="color: {db_status_color}; font-weight: 600; display: inline-flex; align-items: center; gap: 5px;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background-color: {db_status_color}; display: inline-block;"></span>
                    {db_status_text}
                </span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; font-family: 'Inter', sans-serif; font-size: 13px; white-space: nowrap;">
                <span style="color: #64748B; font-weight: 500;">Last ETL Run:</span>
                <span style="color: #0C1E36; font-weight: 600; background: #F1F5F9; padding: 3px 8px; border-radius: 4px;">{last_etl}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; font-family: 'Inter', sans-serif; font-size: 13px; white-space: nowrap;">
                <span style="color: #64748B; font-weight: 500;">Pipeline Status:</span>
                <span style="color: #28a745; font-weight: 600; display: inline-flex; align-items: center; gap: 5px;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background-color: #28a745; display: inline-block;"></span>
                    Healthy
                </span>
            </div>
        </div>
    </div>
    """


def render_kpi_card(title: str, value: str, subtitle: str, tooltip: str = "") -> str:
    """Render a KPI card."""
    html_content = f"""
    <div class="fc-card" title="{tooltip}" style="padding: 18px 12px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 125px; margin-bottom: 0px; cursor: help;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 4px;">
            <span style="font-size: 10px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.2px; line-height: 1.3;">
                {title}
            </span>
        </div>
        <div style="margin-top: 12px; margin-bottom: 4px;">
            <div style="font-size: 24px; font-weight: 700; color: #0C1E36; line-height: 1.1; white-space: nowrap;">{value}</div>
        </div>
        <div style="font-size: 11px; color: #94A3B8; font-weight: 500; line-height: 1.2;">{subtitle}</div>
    </div>
    """
    return clean_html(html_content)


def render_empty_state() -> None:
    """Render warning if filters return no matches."""
    st.markdown(
        """
        <div class="coming-soon-container" style="padding: 50px 20px; margin-top: 15px; border-style: dashed; border-width: 2px;">
            <span class="coming-soon-badge" style="background-color: rgba(220, 53, 69, 0.1); color: #dc3545;">No Data Found</span>
            <h2 class="coming-soon-title" style="color: #dc3545; font-size: 20px;">No Industry Data Matches Active Filters</h2>
            <p class="coming-soon-subtitle" style="max-width: 500px; margin: 0 auto 20px auto;">
                Please adjust your filter options. The selected combination of Fund House, Category, Plan, and Risk yields no matching schemes.
            </p>
            <p style="color: #64748B; font-size: 13px;">Tip: Clear some choices in the selectors above.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def show() -> None:
    """Load industry statistics and render dashboard."""
    try:
        df_aum = load_aum_data()
        df_sip = load_sip_inflows()
        df_folios = load_folios_data()
        df_portfolio = load_portfolio_data()
    except Exception as e:
        st.error(f"Error establishing connection to SQLite database: {e}")
        return

    st.markdown(render_status_bar(), unsafe_allow_html=True)

    st.markdown(
        "<span style='color: #64748B; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;'>Industry Filter Workspace</span>", 
        unsafe_allow_html=True
    )
    
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    
    with f_col1:
        houses = sorted(df_portfolio['fund_house'].unique().tolist())
        selected_houses = st.multiselect("Fund House", options=houses, key="filter_house")
        
    with f_col2:
        categories = sorted(df_portfolio['category'].unique().tolist())
        selected_cats = st.multiselect("Category", options=categories, key="filter_cat")
        
    with f_col3:
        plans = sorted(df_portfolio['plan'].unique().tolist())
        selected_plans = st.multiselect("Plan", options=plans, key="filter_plan")
        
    with f_col4:
        risks = sorted(df_portfolio['risk_category'].unique().tolist())
        selected_risks = st.multiselect("Risk Category", options=risks, key="filter_risk")

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    df_aum_filtered = df_aum.copy()
    if selected_houses:
        df_aum_filtered = df_aum_filtered[df_aum_filtered['fund_house'].isin(selected_houses)]
        
    df_port_filtered = df_portfolio.copy()
    if selected_houses:
        df_port_filtered = df_port_filtered[df_port_filtered['fund_house'].isin(selected_houses)]
    if selected_cats:
        df_port_filtered = df_port_filtered[df_port_filtered['category'].isin(selected_cats)]
    if selected_plans:
        df_port_filtered = df_port_filtered[df_port_filtered['plan'].isin(selected_plans)]
    if selected_risks:
        df_port_filtered = df_port_filtered[df_port_filtered['risk_category'].isin(selected_risks)]

    if df_aum_filtered.empty or df_port_filtered.empty:
        render_empty_state()
        return

    # Total Industry AUM (₹ Lakh Crore)
    latest_aum_date = df_aum['full_date'].max()
    df_aum_latest = df_aum_filtered[df_aum_filtered['full_date'] == latest_aum_date]
    total_industry_aum = df_aum_latest['aum_lakh_crore'].sum()
    
    # Latest Monthly SIP Inflow (₹ Crore)
    latest_sip_row = df_sip.sort_values('month').iloc[-1]
    latest_sip = latest_sip_row['sip_inflow_crore']
    sip_month_str = latest_sip_row['month'].strftime("%b %Y")
    
    # Total Industry Folios
    latest_folios_row = df_folios.sort_values('month').iloc[-1]
    latest_folios = latest_folios_row['total_folios_crore']
    folios_month_str = latest_folios_row['month'].strftime("%b %Y")
    
    # Total Schemes and AMCs
    total_schemes = int(df_aum_latest['num_schemes'].sum())
    tracked_amcs = int(df_aum_latest['fund_house'].nunique())
    analyzed_schemes = int(df_port_filtered['scheme_name'].nunique())

    # KPI columns
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)
    
    with kpi_col1:
        st.markdown(
            render_kpi_card(
                "Total Industry AUM", 
                f"₹ {total_industry_aum:.2f} L Cr", 
                f"As of {latest_aum_date.strftime('%d %b %Y')}",
                "Total aggregate Assets Under Management of the tracked AMCs."
            ), 
            unsafe_allow_html=True
        )
    with kpi_col2:
        st.markdown(
            render_kpi_card(
                "Latest Monthly SIP", 
                f"₹ {latest_sip:,.0f} Cr", 
                f"For month of {sip_month_str}",
                "Latest monthly Systematic Investment Plan inflows."
            ), 
            unsafe_allow_html=True
        )
    with kpi_col3:
        st.markdown(
            render_kpi_card(
                "Total Industry Folios", 
                f"{latest_folios:.2f} Cr", 
                f"Active accounts ({folios_month_str})",
                "Total active mutual fund folio accounts."
            ), 
            unsafe_allow_html=True
        )
    with kpi_col4:
        st.markdown(
            render_kpi_card(
                "Industry AMCs", 
                f"{tracked_amcs}", 
                "Major fund houses covered",
                "Fund houses included in the industry analysis."
            ), 
            unsafe_allow_html=True
        )
    with kpi_col5:
        st.markdown(
            render_kpi_card(
                "Industry Schemes", 
                f"{total_schemes:,}", 
                "Total schemes across selected AMCs",
                "Total schemes managed by the selected AMCs."
            ), 
            unsafe_allow_html=True
        )
    with kpi_col6:
        st.markdown(
            render_kpi_card(
                "Analytics Dataset", 
                f"{analyzed_schemes}", 
                "Schemes used for detailed analysis",
                "Mutual fund schemes used for detailed analytics."
            ), 
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    chart_row1_col1, chart_row1_col2 = st.columns(2)
    
    # AUM Trend Chart
    with chart_row1_col1:
        df_trend_grouped = df_aum_filtered.groupby('full_date')['aum_lakh_crore'].sum().reset_index()
        df_trend_grouped = df_trend_grouped.sort_values('full_date')
        
        fig_trend = px.line(
            df_trend_grouped, 
            x='full_date', 
            y='aum_lakh_crore', 
            title='Industry AUM Trend (₹ Lakh Crore)',
            labels={'full_date': 'Timeline', 'aum_lakh_crore': 'AUM (₹ Lakh Crore)'}
        )
        fig_trend.update_traces(
            line_color='#2E3192', 
            line_width=3, 
            hovertemplate="<b>Timeline</b>: %{x|%d %b %Y}<br><b>AUM</b>: ₹%{y:.2f} Lakh Crore<extra></extra>"
        )
        fig_trend.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_family='Inter, sans-serif',
            font_color='#0C1E36',
            title_font_size=14,
            margin=dict(l=40, r=20, t=50, b=40),
            height=320,
            xaxis=dict(showgrid=False, linecolor='#E2E8F0'),
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9', linecolor='#E2E8F0')
        )
        st.plotly_chart(fig_trend, width="stretch", config={'displayModeBar': False})

    # AUM by AMC Chart
    with chart_row1_col2:
        df_amc_latest = df_aum_filtered[df_aum_filtered['full_date'] == latest_aum_date].copy()
        df_amc_latest = df_amc_latest.sort_values('aum_lakh_crore', ascending=False)
        df_amc_plot = df_amc_latest.iloc[::-1]
        
        fig_amc = px.bar(
            df_amc_plot, 
            x='aum_lakh_crore', 
            y='fund_house', 
            orientation='h', 
            title='Industry AUM by AMC (₹ Lakh Crore)',
            labels={'aum_lakh_crore': 'AUM (₹ Lakh Crore)', 'fund_house': 'AMC'}
        )
        fig_amc.update_traces(
            marker_color='#F58220', 
            opacity=0.9,
            hovertemplate="<b>AMC</b>: %{y}<br><b>AUM</b>: ₹%{x:.2f} Lakh Crore<extra></extra>"
        )
        fig_amc.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_family='Inter, sans-serif',
            font_color='#0C1E36',
            title_font_size=14,
            margin=dict(l=150, r=20, t=50, b=40),
            height=320,
            xaxis=dict(showgrid=True, gridcolor='#F1F5F9', linecolor='#E2E8F0'),
            yaxis=dict(showgrid=False, linecolor='#E2E8F0')
        )
        st.plotly_chart(fig_amc, width="stretch", config={'displayModeBar': False})

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    chart_row2_col1, chart_row2_col2 = st.columns(2)

    # Category Distribution Chart
    with chart_row2_col1:
        df_cat_dist = df_port_filtered.groupby('sub_category').size().reset_index(name='count')
        df_cat_dist = df_cat_dist.sort_values('count', ascending=False)
        
        fig_cat = px.pie(
            df_cat_dist, 
            values='count', 
            names='sub_category', 
            hole=0.5, 
            title='Scheme Category Distribution',
            color_discrete_sequence=['#2E3192', '#F58220', '#4E51C2', '#FF9E4A', '#7D80E5', '#FFAF6A']
        )
        fig_cat.update_traces(
            textinfo='percent+label', 
            textposition='inside',
            hovertemplate="<b>Category</b>: %{label}<br><b>Schemes (Count)</b>: %{value}<br><b>Share</b>: %{percent}<extra></extra>"
        )
        fig_cat.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_family='Inter, sans-serif',
            font_color='#0C1E36',
            title_font_size=14,
            margin=dict(l=20, r=20, t=50, b=20),
            height=320,
            showlegend=False
        )
        st.plotly_chart(fig_cat, width="stretch", config={'displayModeBar': False})

    # Top AMCs Chart
    with chart_row2_col2:
        df_top_amc = df_port_filtered.groupby('fund_house')['aum_crore'].sum().reset_index()
        df_top_amc = df_top_amc.sort_values('aum_crore', ascending=False).head(10)
        df_top_amc_plot = df_top_amc.iloc[::-1]
        
        fig_top_amc = px.bar(
            df_top_amc_plot, 
            x='aum_crore', 
            y='fund_house', 
            orientation='h', 
            title='Top AMCs by Portfolio AUM (₹ Crore)',
            labels={'aum_crore': 'Portfolio AUM (₹ Crore)', 'fund_house': 'AMC'}
        )
        fig_top_amc.update_traces(
            marker_color='#2E3192', 
            opacity=0.9,
            hovertemplate="<b>AMC</b>: %{y}<br><b>Selected Portfolio AUM</b>: ₹%{x:,.0f} Crore<extra></extra>"
        )
        fig_top_amc.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_family='Inter, sans-serif',
            font_color='#0C1E36',
            title_font_size=14,
            margin=dict(l=150, r=20, t=50, b=40),
            height=320,
            xaxis=dict(showgrid=True, gridcolor='#F1F5F9', linecolor='#E2E8F0'),
            yaxis=dict(showgrid=False, linecolor='#E2E8F0')
        )
        st.plotly_chart(fig_top_amc, width="stretch", config={'displayModeBar': False})

    # Executive Insights
    st.markdown(
        "<h3 style='color: #2E3192; font-size: 16px; font-weight: 700; margin-top: 30px; margin-bottom: 15px; font-family: Inter, sans-serif;'>Indian Mutual Fund Industry Executive Insights</h3>", 
        unsafe_allow_html=True
    )
    
    total_amcs = len(df_amc_latest) if not df_amc_latest.empty else 10
    
    def render_insight_card(title: str, description: str) -> str:
        html_content = f"""<div class="fc-card" style="padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); min-height: 110px; display: flex; flex-direction: column; justify-content: flex-start; height: 100%; margin-bottom: 0px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-family: 'Inter', sans-serif;">
<span style="font-weight: 700; color: #2E3192; font-size: 14px;">{title}</span>
</div>
<div style="font-size: 13px; color: #475569; line-height: 1.4; font-family: 'Inter', sans-serif;">
{description}
</div>
</div>"""
        return clean_html(html_content)

    col_ins1, col_ins2 = st.columns(2)
    
    with col_ins1:
        l_amc = df_amc_latest.iloc[0]['fund_house'] if not df_amc_latest.empty else "SBI Mutual Fund"
        l_aum = df_amc_latest.iloc[0]['aum_lakh_crore'] if not df_amc_latest.empty else 12.50
        card1_desc = f"<b>{l_amc}</b> dominates the industry with the highest Assets Under Management of <b>₹ {l_aum:.2f} Lakh Crore</b>."
        st.markdown(render_insight_card("Largest AMC by AUM", card1_desc), unsafe_allow_html=True)
        
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        
        card3_desc = f"Latest monthly SIP inflow reached <b>₹ {latest_sip:,.0f} Crore</b> for the month of <b>{sip_month_str}</b>."
        st.markdown(render_insight_card("Latest SIP Inflow", card3_desc), unsafe_allow_html=True)

    with col_ins2:
        overall_aum_sum = df_amc_latest['aum_lakh_crore'].sum() if not df_amc_latest.empty else 1.0
        mkt_share_pct = (df_amc_latest.iloc[0]['aum_lakh_crore'] / overall_aum_sum) * 100 if not df_amc_latest.empty else 20.0
        card2_desc = f"<b>{l_amc}</b> currently controls the largest market share of <b>{mkt_share_pct:.1f}%</b> among the available AMCs."
        st.markdown(render_insight_card("AUM Market Share", card2_desc), unsafe_allow_html=True)
        
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        
        card4_desc = f"The platform currently tracks <b>{total_amcs}</b> fund houses and <b>{total_schemes:,}</b> schemes in the mutual fund industry."
        st.markdown(render_insight_card("Industry Coverage", card4_desc), unsafe_allow_html=True)


if __name__ == "__main__":
    render_layout("Dashboard (Industry Overview)", show)
