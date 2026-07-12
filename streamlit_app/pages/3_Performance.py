"""Performance page for Mutual Fund Analytics."""
import sys
from pathlib import Path
import sqlite3
from typing import Dict, Any, List

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from streamlit_app.components.layout import render_layout
from streamlit_app.database import get_db_connection
from streamlit_app.config import DB_PATH
from streamlit_app.helpers import clean_html

@st.cache_data
def load_portfolio_performance_data() -> pd.DataFrame:
    """Load fund master list and performance stats."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    query = """
        SELECT f.fund_id, f.amfi_code, f.fund_house, f.scheme_name, f.category, 
               f.sub_category, f.plan, f.risk_category, f.benchmark, f.fund_manager,
               p.return_1yr_pct, p.return_3yr_pct, p.return_5yr_pct, 
               p.sharpe_ratio, p.sortino_ratio, p.alpha, p.beta, 
               p.std_dev_ann_pct, p.max_drawdown_pct, p.aum_crore, p.expense_ratio_pct
        FROM dim_fund f
        JOIN fact_performance p ON f.fund_id = p.fund_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data
def load_nav_vs_benchmark_data(fund_id: int, index_name: str) -> pd.DataFrame:
    """Load NAV and benchmark data for comparison."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    
    # Load Fund NAV
    nav_query = """
        SELECT d.full_date as date, n.nav
        FROM fact_nav n
        JOIN dim_date d ON n.date_id = d.date_id
        WHERE n.fund_id = ?
    """
    df_nav = pd.read_sql_query(nav_query, conn, params=(fund_id,))
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    
    # Load Benchmark Index
    bench_query = """
        SELECT date, close_value as benchmark
        FROM stg_benchmark_indices
        WHERE index_name = ?
    """
    df_bench = pd.read_sql_query(bench_query, conn, params=(index_name,))
    df_bench['date'] = pd.to_datetime(df_bench['date'])
    
    conn.close()
    
    df_nav = df_nav.sort_values('date').reset_index(drop=True)
    df_bench = df_bench.sort_values('date').reset_index(drop=True)
    
    if not df_nav.empty and not df_bench.empty:
        min_date = min(df_nav['date'].min(), df_bench['date'].min())
        max_date = max(df_nav['date'].max(), df_bench['date'].max())
        all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
        
        df_nav = df_nav.set_index('date').reindex(all_dates)
        df_nav.index.name = 'date'
        df_nav = df_nav.reset_index()
        df_nav['nav'] = df_nav['nav'].ffill()
        
        df_bench = df_bench.set_index('date').reindex(all_dates)
        df_bench.index.name = 'date'
        df_bench = df_bench.reset_index()
        df_bench['benchmark'] = df_bench['benchmark'].ffill()
        
        df_merged = pd.merge(df_nav, df_bench, on='date', how='inner')
        df_merged = df_merged.dropna(subset=['nav', 'benchmark']).reset_index(drop=True)
    else:
        df_merged = pd.merge(df_nav, df_bench, on='date', how='inner')
        df_merged = df_merged.sort_values('date').reset_index(drop=True)
        
    return df_merged


BENCHMARK_MAP = {
    'NIFTY 100 TRI': 'NIFTY100',
    'CRISIL Short Term Bond Index': 'CRISIL_GILT',
    'NIFTY Midcap 150 TRI': 'NIFTY_MIDCAP150',
    'BSE 250 SmallCap TRI': 'BSE_SMALLCAP',
    'CRISIL Liquid Fund AI Index': 'CRISIL_LIQUID',
    'NIFTY 50 TRI': 'NIFTY50',
    'NIFTY 500 TRI': 'NIFTY500',
    'CRISIL Dynamic Gilt Index': 'CRISIL_GILT',
    'NIFTY Midcap 50 TRI': 'NIFTY_MIDCAP150',
    'NIFTY Large Midcap 250 TRI': 'NIFTY500'
}


def render_perf_kpi_card(title: str, value: str, icon: str) -> str:
    """Generate HTML for performance KPI card."""
    html_content = f"""
    <div class="fc-card" style="padding: 12px; border-radius: 10px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 2px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 80px; margin-bottom: 0px; text-align: center; height: 100%;">
        <div style="font-size: 10px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; line-height: 1.1; margin-bottom: 4px;">
            {icon} {title}
        </div>
        <div style="font-size: 18px; font-weight: 700; color: #0C1E36; line-height: 1.1; margin-top: auto; margin-bottom: auto; white-space: nowrap;">
            {value}
        </div>
    </div>
    """
    return clean_html(html_content)


def render_insight_card(title: str, description: str) -> str:
    """Generate HTML for Insight card."""
    html_content = f"""
    <div class="fc-card" style="padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); min-height: 108px; display: flex; flex-direction: column; justify-content: flex-start; height: 100%; margin-bottom: 0px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-family: 'Inter', sans-serif;">
            <span style="font-weight: 700; color: #2E3192; font-size: 14px;">{title}</span>
        </div>
        <div style="font-size: 13px; color: #475569; line-height: 1.4; font-family: 'Inter', sans-serif;">
            {description}
        </div>
    </div>
    """
    return clean_html(html_content)


def render_empty_state() -> None:
    """Render empty-state when no funds match filters."""
    st.markdown(
        """
        <div class="coming-soon-container" style="padding: 50px 20px; margin-top: 15px; border-style: dashed; border-width: 2px;">
            <span class="coming-soon-badge" style="background-color: rgba(220, 53, 69, 0.1); color: #dc3545;">No Data Found</span>
            <h2 class="coming-soon-title" style="color: #dc3545; font-size: 20px;">No Funds Match Selected Filters</h2>
            <p class="coming-soon-subtitle" style="max-width: 500px; margin: 0 auto 20px auto;">
                Please adjust your filter selections. The active combination of Fund House, Category, Plan, and Risk yields zero mutual funds.
            </p>
            <p style="color: #64748B; font-size: 13px;">Tip: Clear some dropdown items to expand search coverage.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def show() -> None:
    """Render performance dashboard."""
    try:
        df_portfolio = load_portfolio_performance_data()
    except Exception as e:
        st.error(f"Error establishing connection to SQLite database: {e}")
        return

    st.markdown(
        "<span style='color: #64748B; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;'>Performance Filters Workspace</span>", 
        unsafe_allow_html=True
    )
    
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    
    with f_col1:
        houses = sorted(df_portfolio['fund_house'].unique().tolist())
        selected_houses = st.multiselect("Fund House", options=houses, key="perf_filter_house")
        
    with f_col2:
        categories = sorted(df_portfolio['category'].unique().tolist())
        selected_cats = st.multiselect("Category", options=categories, key="perf_filter_cat")
        
    with f_col3:
        plans = sorted(df_portfolio['plan'].unique().tolist())
        selected_plans = st.multiselect("Plan", options=plans, key="perf_filter_plan")
        
    with f_col4:
        risks = sorted(df_portfolio['risk_category'].unique().tolist())
        selected_risks = st.multiselect("Risk Category", options=risks, key="perf_filter_risk")

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    df_filtered = df_portfolio.copy()
    if selected_houses:
        df_filtered = df_filtered[df_filtered['fund_house'].isin(selected_houses)]
    if selected_cats:
        df_filtered = df_filtered[df_filtered['category'].isin(selected_cats)]
    if selected_plans:
        df_filtered = df_filtered[df_filtered['plan'].isin(selected_plans)]
    if selected_risks:
        df_filtered = df_filtered[df_filtered['risk_category'].isin(selected_risks)]

    if df_filtered.empty:
        render_empty_state()
        return

    avg_1y = df_filtered['return_1yr_pct'].mean()
    avg_3y = df_filtered['return_3yr_pct'].mean()
    avg_5y = df_filtered['return_5yr_pct'].mean()
    avg_sharpe = df_filtered['sharpe_ratio'].mean()
    avg_sortino = df_filtered['sortino_ratio'].mean()
    avg_alpha = df_filtered['alpha'].mean()
    avg_beta = df_filtered['beta'].mean()
    avg_drawdown = df_filtered['max_drawdown_pct'].mean()

    kpi_cols = st.columns(8)
    metrics = [
        ("Avg 1Y Return (%)", f"{avg_1y:.2f}%", ""),
        ("Avg 3Y Return (%)", f"{avg_3y:.2f}%", ""),
        ("Avg 5Y CAGR (%)", f"{avg_5y:.2f}%", ""),
        ("Avg Sharpe", f"{avg_sharpe:.2f}", ""),
        ("Avg Sortino", f"{avg_sortino:.2f}", ""),
        ("Avg Alpha (%)", f"{avg_alpha:.2f}%", ""),
        ("Avg Beta", f"{avg_beta:.2f}", ""),
        ("Avg Max DD (%)", f"{avg_drawdown:.2f}%", "")
    ]

    for col, (title, val, icon) in zip(kpi_cols, metrics):
        with col:
            st.markdown(render_perf_kpi_card(title, val, icon), unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600; margin-top: 10px; margin-bottom: 5px;'>Risk vs Return Analysis</h4>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 12px; color: #64748B; margin-top: 0; margin-bottom: 15px;'>Bubble sizes correspond to Asset Under Management (AUM). Drag to zoom, double-click to reset.</p>", unsafe_allow_html=True)
    
    fig_scatter = px.scatter(
        df_filtered,
        x='return_1yr_pct',
        y='std_dev_ann_pct',
        size='aum_crore',
        color='category',
        hover_name='scheme_name',
        labels={
            'return_1yr_pct': '1-Year Return (%)',
            'std_dev_ann_pct': 'Annualized Risk (Std Dev %)',
            'category': 'Asset Category'
        },
        color_discrete_map={'Equity': '#2E3192', 'Debt': '#F58220'},
        size_max=35
    )
    
    fig_scatter.update_traces(
        customdata=df_filtered[[
            'fund_house', 'category', 'plan', 'sharpe_ratio', 
            'sortino_ratio', 'alpha', 'beta', 'expense_ratio_pct', 'aum_crore'
        ]].values,
        hovertemplate="""<b>%{hovertext}</b><br><br>
<b>Fund House</b>: %{customdata[0]}<br>
<b>Category</b>: %{customdata[1]}<br>
<b>Plan</b>: %{customdata[2]}<br>
<b>1-Yr Return</b>: %{x:.2f}%<br>
<b>Risk (Std Dev)</b>: %{y:.2f}%<br>
<b>Sharpe Ratio</b>: %{customdata[3]:.2f}<br>
<b>Sortino Ratio</b>: %{customdata[4]:.2f}<br>
<b>Alpha</b>: %{customdata[5]:.2f}%<br>
<b>Beta</b>: %{customdata[6]:.2f}<br>
<b>Expense Ratio</b>: %{customdata[7]:.2f}%<br>
<b>AUM (₹ Crore)</b>: %{customdata[8]:,.1f}<br>
<extra></extra>"""
    )
    
    fig_scatter.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_family='Inter, sans-serif',
        font_color='#0C1E36',
        margin=dict(l=40, r=20, t=10, b=40),
        height=380,
        xaxis=dict(showgrid=True, gridcolor='#F1F5F9', linecolor='#E2E8F0'),
        yaxis=dict(showgrid=True, gridcolor='#F1F5F9', linecolor='#E2E8F0')
    )
    st.plotly_chart(fig_scatter, width="stretch", config={'displayModeBar': True})

    st.markdown("<div style='margin-bottom: 35px;'></div>", unsafe_allow_html=True)

    st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600; margin-top: 10px; margin-bottom: 5px;'>Fund NAV vs Benchmark Performance</h4>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 12px; color: #64748B; margin-top: 0; margin-bottom: 15px;'>Compare historical daily NAV closes of a selected fund against its index benchmark value.</p>", unsafe_allow_html=True)
    
    compare_fund = st.selectbox(
        "Select Mutual Fund",
        options=sorted(df_filtered['scheme_name'].tolist()),
        key="perf_compare_fund_select"
    )
    
    if compare_fund:
        fund_row = df_filtered[df_filtered['scheme_name'] == compare_fund].iloc[0]
        fund_id = int(fund_row['fund_id'])
        bench_desc = fund_row['benchmark']
        
        index_name = BENCHMARK_MAP.get(bench_desc, "NIFTY50")
        
        try:
            df_merged = load_nav_vs_benchmark_data(fund_id, index_name)
            
            if df_merged.empty:
                st.warning(f"No overlapping date records found between the fund and benchmark index {index_name}.")
            else:
                fig_bench = make_subplots(specs=[[{"secondary_y": True}]])
                
                # Fund NAV trace
                fig_bench.add_trace(
                    go.Scatter(
                        x=df_merged['date'], 
                        y=df_merged['nav'], 
                        mode='lines',
                        name="Fund NAV (₹)", 
                        line=dict(color='#2E3192', width=2.5),
                        hovertemplate="<b>Date</b>: %{x|%d %b %Y}<br><b>NAV</b>: ₹%{y:.2f}<extra></extra>"
                    ), 
                    secondary_y=False
                )
                
                # Benchmark trace
                fig_bench.add_trace(
                    go.Scatter(
                        x=df_merged['date'], 
                        y=df_merged['benchmark'], 
                        mode='lines',
                        name=f"Benchmark ({index_name})", 
                        line=dict(color='#F58220', width=2, dash='dot'),
                        hovertemplate="<b>Date</b>: %{x|%d %b %Y}<br><b>Index Value</b>: %{y:,.2f}<extra></extra>"
                    ), 
                    secondary_y=True
                )
                
                fig_bench.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font_family='Inter, sans-serif',
                    font_color='#0C1E36',
                    margin=dict(l=40, r=45, t=10, b=45),
                    height=360,
                    xaxis=dict(showgrid=False, linecolor='#E2E8F0'),
                    yaxis=dict(showgrid=True, gridcolor='#F1F5F9', linecolor='#E2E8F0', title="Fund NAV (₹)"),
                    yaxis2=dict(showgrid=False, linecolor='#E2E8F0', title=f"Index Value ({index_name})"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                fig_bench.update_xaxes(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(count=6, label="6m", step="month", stepmode="backward"),
                            dict(count=1, label="1y", step="year", stepmode="backward"),
                            dict(count=3, label="3y", step="year", stepmode="backward"),
                            dict(step="all", label="All")
                        ]),
                        bgcolor="#F8FAFC",
                        activecolor="#E2E8F0",
                        font=dict(size=11, family="Inter", color="#0C1E36")
                    )
                )
                st.plotly_chart(fig_bench, width="stretch", config={'displayModeBar': False})
        except Exception as e:
            st.warning(f"Unable to compare NAV with index benchmark: {e}")

    st.markdown("<div style='margin-bottom: 35px;'></div>", unsafe_allow_html=True)

    st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600; margin-top: 10px; margin-bottom: 5px;'>Top Performing Funds</h4>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 12px; color: #64748B; margin-top: 0; margin-bottom: 15px;'>Interactive list of selected funds. Use sorting, column filters, and search to inspect details.</p>", unsafe_allow_html=True)
    
    df_display = df_filtered[[
        'scheme_name', 'fund_house', 'category', 'plan', 
        'return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 
        'sharpe_ratio', 'sortino_ratio', 'alpha', 'beta', 
        'expense_ratio_pct', 'aum_crore'
    ]].copy()
    
    df_display.columns = [
        'Fund Name', 'Fund House', 'Category', 'Plan', 
        'Return 1Y (%)', 'Return 3Y (%)', 'Return 5Y (%)', 
        'Sharpe Ratio', 'Sortino Ratio', 'Alpha (%)', 'Beta', 'Expense Ratio (%)', 'AUM (₹ Crore)'
    ]
    
    df_display = df_display.sort_values('Return 1Y (%)', ascending=False)
    st.dataframe(df_display, width="stretch", hide_index=True)

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    dt_col1, dt_col2 = st.columns([3, 1])
    
    with dt_col1:
        drill_fund = st.selectbox(
            "Select a Fund to drill-through to Daily NAV Analytics:",
            options=[""] + sorted(df_filtered['scheme_name'].tolist()),
            key="perf_drill_through_select",
            help="Choose a fund to save in system session state and redirect to the NAV Analytics panel."
        )
    with dt_col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if drill_fund:
            fund_data = df_filtered[df_filtered['scheme_name'] == drill_fund].iloc[0]
            st.session_state.selected_fund_id = int(fund_data['fund_id'])
            st.session_state.selected_amfi_code = int(fund_data['amfi_code'])
            st.session_state.selected_fund_name = str(fund_data['scheme_name'])
            
            if st.button("View Daily NAV Analysis", type="primary", width="stretch"):
                st.switch_page("pages/2_NAV_Analytics.py")
        else:
            st.button("View Daily NAV Analysis", type="primary", disabled=True, width="stretch")

    st.markdown("<div style='margin-bottom: 35px;'></div>", unsafe_allow_html=True)

    dist_col1, dist_col2 = st.columns(2)
    
    with dist_col1:
        mean_ret = df_filtered['return_1yr_pct'].mean()
        median_ret = df_filtered['return_1yr_pct'].median()
        
        fig_dist = px.histogram(
            df_filtered, 
            x='return_1yr_pct', 
            nbins=12, 
            title='Distribution of 1-Year Returns',
            labels={'return_1yr_pct': '1-Year Return (%)', 'count': 'Frequency'}
        )
        fig_dist.update_traces(
            marker_color='#F58220', 
            opacity=0.8,
            hovertemplate="<b>Return Range</b>: %{x}%<br><b>Fund Count</b>: %{y}<extra></extra>"
        )
        
        fig_dist.add_vline(x=mean_ret, line_dash='dash', line_color='#2E3192', line_width=2)
        fig_dist.add_vline(x=median_ret, line_dash='dot', line_color='#0C1E36', line_width=2)
        
        fig_dist.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_family='Inter, sans-serif',
            font_color='#0C1E36',
            title_font_size=14,
            margin=dict(l=40, r=20, t=50, b=40),
            height=300,
            xaxis=dict(showgrid=False, linecolor='#E2E8F0'),
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9', linecolor='#E2E8F0', title='Fund Count'),
            annotations=[
                dict(x=mean_ret, y=0.9, yref='paper', text=f"Mean: {mean_ret:.1f}%", showarrow=False, font=dict(color='#2E3192', size=10), bgcolor='white'),
                dict(x=median_ret, y=0.7, yref='paper', text=f"Median: {median_ret:.1f}%", showarrow=False, font=dict(color='#0C1E36', size=10), bgcolor='white')
            ]
        )
        st.plotly_chart(fig_dist, width="stretch", config={'displayModeBar': False})
        
    with dist_col2:
        mean_risk = df_filtered['std_dev_ann_pct'].mean()
        median_risk = df_filtered['std_dev_ann_pct'].median()
        
        fig_risk = px.histogram(
            df_filtered, 
            x='std_dev_ann_pct', 
            nbins=12, 
            title='Distribution of Annualized Risk (Std Dev)',
            labels={'std_dev_ann_pct': 'Annualized Risk (Std Dev %)', 'count': 'Frequency'}
        )
        fig_risk.update_traces(
            marker_color='#2E3192', 
            opacity=0.8,
            hovertemplate="<b>Risk Range</b>: %{x}%<br><b>Fund Count</b>: %{y}<extra></extra>"
        )
        
        fig_risk.add_vline(x=mean_risk, line_dash='dash', line_color='#F58220', line_width=2)
        fig_risk.add_vline(x=median_risk, line_dash='dot', line_color='#0C1E36', line_width=2)
        
        fig_risk.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_family='Inter, sans-serif',
            font_color='#0C1E36',
            title_font_size=14,
            margin=dict(l=40, r=20, t=50, b=40),
            height=300,
            xaxis=dict(showgrid=False, linecolor='#E2E8F0'),
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9', linecolor='#E2E8F0', title='Fund Count'),
            annotations=[
                dict(x=mean_risk, y=0.9, yref='paper', text=f"Mean: {mean_risk:.1f}%", showarrow=False, font=dict(color='#F58220', size=10), bgcolor='white'),
                dict(x=median_risk, y=0.7, yref='paper', text=f"Median: {median_risk:.1f}%", showarrow=False, font=dict(color='#0C1E36', size=10), bgcolor='white')
            ]
        )
        st.plotly_chart(fig_risk, width="stretch", config={'displayModeBar': False})

    st.markdown("<div style='margin-bottom: 35px;'></div>", unsafe_allow_html=True)

    st.markdown(
        "<h3 style='color: #2E3192; font-size: 16px; font-weight: 700; margin-top: 10px; margin-bottom: 20px; font-family: Inter, sans-serif;'>Executive Performance Insights</h3>", 
        unsafe_allow_html=True
    )
    
    insights = []
    
    h_ret_idx = df_filtered['return_1yr_pct'].idxmax()
    h_ret_fund = df_filtered.loc[h_ret_idx]
    insights.append({
        "title": "Highest Returning Fund",
        "desc": f"<b>{h_ret_fund['scheme_name']}</b> generated the highest 1-Year Return of <b>{h_ret_fund['return_1yr_pct']:.2f}%</b> in the selection."
    })
    
    l_dd_idx = df_filtered['max_drawdown_pct'].idxmin()
    l_dd_fund = df_filtered.loc[l_dd_idx]
    insights.append({
        "title": "Best Downside Protection",
        "desc": f"<b>{l_dd_fund['scheme_name']}</b> features the lowest Max Drawdown of <b>{l_dd_fund['max_drawdown_pct']:.2f}%</b>, indicating strong defense."
    })
    
    h_sharpe_idx = df_filtered['sharpe_ratio'].idxmax()
    h_sharpe_fund = df_filtered.loc[h_sharpe_idx]
    insights.append({
        "title": "Highest Sharpe Ratio",
        "desc": f"<b>{h_sharpe_fund['scheme_name']}</b> achieved a Sharpe Ratio of <b>{h_sharpe_fund['sharpe_ratio']:.2f}</b>, leading in risk-adjusted performance."
    })
    
    h_alpha_idx = df_filtered['alpha'].idxmax()
    h_alpha_fund = df_filtered.loc[h_alpha_idx]
    insights.append({
        "title": "Highest Excess Return (Alpha)",
        "desc": f"<b>{h_alpha_fund['scheme_name']}</b> generated the highest Alpha of <b>{h_alpha_fund['alpha']:.2f}%</b> above its benchmark."
    })
    
    l_exp_idx = df_filtered['expense_ratio_pct'].idxmin()
    l_exp_fund = df_filtered.loc[l_exp_idx]
    insights.append({
        "title": "Lowest Expense Ratio",
        "desc": f"<b>{l_exp_fund['scheme_name']}</b> offers the most cost-effective entry with an Expense Ratio of <b>{l_exp_fund['expense_ratio_pct']:.2f}%</b>."
    })
    
    h_aum_idx = df_filtered['aum_crore'].idxmax()
    h_aum_fund = df_filtered.loc[h_aum_idx]
    insights.append({
        "title": "Largest Selected AUM scale",
        "desc": f"<b>{h_aum_fund['scheme_name']}</b> holds the largest asset scale with an AUM of <b>₹ {h_aum_fund['aum_crore']:,.1f} Crore</b>."
    })

    ins_col1, ins_col2, ins_col3 = st.columns(3)
    with ins_col1:
        st.markdown(render_insight_card(insights[0]['title'], insights[0]['desc']), unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        st.markdown(render_insight_card(insights[3]['title'], insights[3]['desc']), unsafe_allow_html=True)
        
    with ins_col2:
        st.markdown(render_insight_card(insights[1]['title'], insights[1]['desc']), unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        st.markdown(render_insight_card(insights[4]['title'], insights[4]['desc']), unsafe_allow_html=True)
        
    with ins_col3:
        st.markdown(render_insight_card(insights[2]['title'], insights[2]['desc']), unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        st.markdown(render_insight_card(insights[5]['title'], insights[5]['desc']), unsafe_allow_html=True)


if __name__ == "__main__":
    render_layout("Fund Performance Analytics", show)
