"""NAV Analytics page."""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from streamlit_app.components.layout import render_layout
from streamlit_app.database import get_db_connection
from streamlit_app.helpers import clean_html
import importlib
import streamlit_app.services.nav_service as nav_service
importlib.reload(nav_service)

from streamlit_app.services.nav_service import (
    load_nav_history,
    nav_statistics,
    calculate_daily_returns,
    daily_return_statistics,
    calculate_rolling_returns,
    get_rolling_return_statistics,
    calculate_drawdown,
    get_drawdown_statistics,
    monthly_nav,
    calculate_monthly_returns,
    get_monthly_return_statistics,
    generate_dynamic_insights,
)

def render_nav_kpi_card(title: str, value: str, subtitle: str, icon: str) -> str:
    """Generate HTML for NAV KPI card."""
    html_content = f"""
    <div class="fc-card" style="padding: 16px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 100px; height: 100%; margin-bottom: 0px;">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 4px;">
            <span style="font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                {title}
            </span>
        </div>
        <div style="margin-top: 10px; margin-bottom: 2px;">
            <div style="font-size: 20px; font-weight: 700; color: #0C1E36; line-height: 1.1; white-space: nowrap;">
                {value}
            </div>
        </div>
        <div style="font-size: 10px; color: #94A3B8; font-weight: 500;">
            {subtitle}
        </div>
    </div>
    """
    return clean_html(html_content)


def render_return_kpi_card(title: str, value: str, subtitle: str, color: str, icon: str) -> str:
    """Generate HTML for return metric card."""
    html_content = f"""
    <div class="fc-card" style="padding: 16px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 90px; height: 100%; margin-bottom: 0px; border-left: 4px solid {color};">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 4px;">
            <span style="font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
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
    """Render the NAV Analytics dashboard."""
    fund_id = st.session_state.get("selected_fund_id")

    if fund_id is None:
        st.warning(
            "⚠️ Please select a fund from the Performance page first."
        )
        return

    conn = get_db_connection()
    fund = pd.read_sql_query(
        """
        SELECT
            scheme_name,
            fund_house,
            category,
            plan,
            benchmark,
            risk_category
        FROM dim_fund
        WHERE fund_id = ?
        """,
        conn,
        params=(fund_id,)
    )
    conn.close()

    if fund.empty:
        st.error("Fund not found.")
        return

    info = fund.iloc[0]

    st.markdown(
        """
        <h2 style="color:#0C1E36;margin-bottom:5px;">
            NAV Analytics
        </h2>
        <p style="color:#64748B;font-size:16px;">
            Historical NAV analysis for the selected mutual fund
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="fc-card" style="padding: 24px; border: 1px solid #E2E8F0; background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 15px;">
                <div>
                    <span style="background: rgba(46, 49, 146, 0.1); color: #2E3192; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; display: inline-block; margin-bottom: 10px;">
                        {info['category']}
                    </span>
                    <h3 style="color: #0C1E36; margin: 0 0 6px 0; font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 700;">
                        {info['scheme_name']}
                    </h3>
                    <div style="font-size: 13px; color: #64748B; font-weight: 500; margin-bottom: 12px;">
                        {info['fund_house']}
                    </div>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap; font-size: 13px; color: #475569; font-family: 'Inter', sans-serif;">
                        <span><strong>Plan:</strong> {info['plan']}</span>
                        <span>•</span>
                        <span><strong>Benchmark:</strong> {info['benchmark']}</span>
                    </div>
                </div>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 20px; min-width: 140px; text-align: center;">
                    <div style="font-size: 10px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                        Risk Category
                    </div>
                    <div style="font-size: 18px; font-weight: 700; color: #F58220; display: flex; align-items: center; justify-content: center; gap: 5px;">
                        {info['risk_category']}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "<span style='color: #64748B; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;'>Date range control workspace</span>", 
        unsafe_allow_html=True
    )
    
    col_filter1, col_filter2 = st.columns([3, 1])
    with col_filter1:
        range_mode = st.radio(
            "Select Analysis Date Range Mode:",
            options=[
                "Platform Standard (Jan 2022 - May 2026) - Clean & Verified",
                "⏳ Full History (Includes historical AMFI & live records)"
            ],
            index=0,
            horizontal=True,
            help="Standard mode filters out database code mismatches, spikes, and weekend data. Full History displays all dates but may contain level shifts."
        )
    
    filter_standard = "Platform Standard" in range_mode

    nav_df = load_nav_history(fund_id, filter_standard=filter_standard)

    # Level shift check
    has_discontinuity = False
    if not filter_standard and len(nav_df) >= 2:
        pct_change = nav_df["nav"].pct_change().abs()
        if (pct_change > 0.20).any():
            has_discontinuity = True

    if has_discontinuity:
        st.markdown(
            """
            <div class="coming-soon-container" style="padding: 16px 20px; text-align: left; border-color: #F58220; margin-top: 10px; margin-bottom: 20px; background-color: #FFFDF9; display: flex; align-items: flex-start; gap: 15px;">
                <div style="font-size: 24px; line-height: 1; margin-top: 2px;">⚠️</div>
                <div>
                    <h4 style="color: #D97706; margin: 0 0 4px 0; font-size: 14px; font-weight: 700;">Data Discontinuity Warning</h4>
                    <p style="color: #64748B; font-size: 12px; margin: 0; line-height: 1.4;">
                        A major level shift (>20% daily change) has been detected in the historical database series for this fund. 
                        This occurs due to plan changes, merges, or database mapping differences in raw AMFI source files. 
                        <strong>We recommend switching back to the Platform Standard (2022-2026) mode</strong> for clean analytics.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    stats = nav_statistics(nav_df)

    latest_date = nav_df['full_date'].iloc[-1].strftime('%d %b %Y') if len(nav_df) > 0 else "N/A"
    
    max_idx = nav_df['nav'].idxmax() if len(nav_df) > 0 else None
    max_date = nav_df.loc[max_idx, 'full_date'].strftime('%d %b %Y') if max_idx is not None else "N/A"
    
    min_idx = nav_df['nav'].idxmin() if len(nav_df) > 0 else None
    min_date = nav_df.loc[min_idx, 'full_date'].strftime('%d %b %Y') if min_idx is not None else "N/A"

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            render_nav_kpi_card("Latest NAV (₹)", f"₹ {stats['latest']:.2f}", f"As of {latest_date}", ""),
            unsafe_allow_html=True
        )
    with k2:
        st.markdown(
            render_nav_kpi_card("Highest NAV (₹)", f"₹ {stats['highest']:.2f}", f"Peak on {max_date}", ""),
            unsafe_allow_html=True
        )
    with k3:
        st.markdown(
            render_nav_kpi_card("Lowest NAV (₹)", f"₹ {stats['lowest']:.2f}", f"Trough on {min_date}", ""),
            unsafe_allow_html=True
        )
    with k4:
        st.markdown(
            render_nav_kpi_card("Average NAV (₹)", f"₹ {stats['average']:.2f}", "Mean value over period", ""),
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

    if len(nav_df) < 2:
        st.warning("⚠️ Insufficient NAV data available for this date selection to calculate analytics.")
        return

    drawdown_precomputed = calculate_drawdown(nav_df)
    max_dd = drawdown_precomputed["drawdown_pct"].min()

    total_return = 0.0
    if len(nav_df) >= 2:
        total_return = (nav_df["nav"].iloc[-1] - nav_df["nav"].iloc[0]) / nav_df["nav"].iloc[0] * 100

    tab_trend, tab_rolling, tab_dist, tab_drawdown, tab_monthly, tab_stats = st.tabs([
        "NAV Trend",
        "Rolling Returns Analysis",
        "Return Distributions",
        "Risk & Drawdown",
        "Monthly NAV Analysis",
        "Statistics & Insights"
    ])

    # TAB 1: NAV Trend
    with tab_trend:
        st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600; margin-top: 10px; margin-bottom: 15px;'>Historical NAV Trend</h4>", unsafe_allow_html=True)
        
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=nav_df["full_date"],
                y=nav_df["nav"],
                mode="lines",
                name="NAV",
                line=dict(
                    color="#2E3192",
                    width=2.5
                ),
                hovertemplate="<b>%{x|%d %b %Y}</b><br>NAV: ₹%{y:.2f}<extra></extra>"
            )
        )
        fig.update_layout(
            template="plotly_white",
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_family='Inter, sans-serif',
            font_color='#0C1E36',
            height=400,
            margin=dict(l=40, r=20, t=10, b=40),
            hovermode="x unified",
            xaxis=dict(
                showgrid=False, 
                linecolor='#E2E8F0',
                title=dict(text="Date", font=dict(size=12, color='#64748B'))
            ),
            yaxis=dict(
                showgrid=True, 
                gridcolor='#F1F5F9', 
                linecolor='#E2E8F0',
                title=dict(text="NAV (₹)", font=dict(size=12, color='#64748B'))
            ),
            showlegend=False,
        )
        fig.update_xaxes(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="All"),
                ],
                bgcolor='#F8FAFC',
                activecolor='#E2E8F0',
                font=dict(size=11, color='#0C1E36')
            ),
        )
        st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})

    # TAB 2: Rolling Returns Analysis
    with tab_rolling:
        st.markdown(
            """
            <h4 style="color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600; margin-top: 10px; margin-bottom: 5px;">
                Rolling Returns Analysis
            </h4>
            <p style="font-size: 13px; color: #64748B; line-height: 1.4; margin-bottom: 20px;">
                Rolling returns show the compound return of the mutual fund over a fixed historical window rolled forward daily. 
                This offers a truer picture of a fund's historical return consistency compared to static point-to-point trailing returns, which are highly sensitive to start and end dates.
            </p>
            """,
            unsafe_allow_html=True
        )

        col_win, col_spacer = st.columns([1, 2])
        with col_win:
            roll_window = st.selectbox(
                "Select Rolling Analysis Window:",
                options=[30, 90, 180, 365],
                format_func=lambda x: f"{x} Days (1 Year)" if x == 365 else f"{x} Days",
                key="nav_roll_window_select_new"
            )

        roll_df = calculate_rolling_returns(nav_df, window=roll_window)

        if roll_df.empty:
            st.warning(f"⚠️ Insufficient historical NAV data to calculate rolling returns for the selected {roll_window}-day window.")
        else:
            roll_stats = get_rolling_return_statistics(roll_df)

            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
            rc1, rc2, rc3, rc4, rc5 = st.columns(5)
            with rc1:
                st.markdown(
                    render_return_kpi_card(
                        "Current Return",
                        f"{roll_stats['current_return']:.2f}%",
                        f"As of {roll_stats['current_date']}",
                        "#2E3192",
                        ""
                    ),
                    unsafe_allow_html=True
                )
            with rc2:
                st.markdown(
                    render_return_kpi_card(
                        "Average Return",
                        f"{roll_stats['average']:.2f}%",
                        "Mean rolling change",
                        "#3B82F6",
                        ""
                    ),
                    unsafe_allow_html=True
                )
            with rc3:
                st.markdown(
                    render_return_kpi_card(
                        "Volatility",
                        f"{roll_stats['volatility']:.2f}%",
                        "Std dev of returns",
                        "#64748B",
                        ""
                    ),
                    unsafe_allow_html=True
                )
            with rc4:
                st.markdown(
                    render_return_kpi_card(
                        "Maximum Return",
                        f"+{roll_stats['max_return']:.2f}%",
                        f"Peak on {roll_stats['max_date']}",
                        "#10B981",
                        ""
                    ),
                    unsafe_allow_html=True
                )
            with rc5:
                st.markdown(
                    render_return_kpi_card(
                        "Minimum Return",
                        f"{roll_stats['min_return']:.2f}%",
                        f"Trough on {roll_stats['min_date']}",
                        "#EF4444",
                        ""
                    ),
                    unsafe_allow_html=True
                )

            st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

            fig_roll = go.Figure()
            fig_roll.add_trace(
                go.Scatter(
                    x=roll_df["full_date"],
                    y=roll_df["rolling_return_pct"],
                    mode="lines",
                    name=f"{roll_window}D Rolling Return",
                    line=dict(
                        color="#F58220", 
                        width=2.2
                    ),
                    hovertemplate="<b>%{x|%d %b %Y}</b><br>Rolling Return: %{y:.2f}%<extra></extra>"
                )
            )
            fig_roll.update_layout(
                template="plotly_white",
                plot_bgcolor='white',
                paper_bgcolor='white',
                font_family='Inter, sans-serif',
                font_color='#0C1E36',
                height=400,
                margin=dict(l=40, r=20, t=15, b=40),
                hovermode="x unified",
                xaxis=dict(
                    showgrid=False,
                    linecolor='#E2E8F0',
                    title=dict(text="Date", font=dict(size=12, color='#64748B'))
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#F1F5F9',
                    linecolor='#E2E8F0',
                    title=dict(text="Rolling Return (%)", font=dict(size=12, color='#64748B'))
                ),
                showlegend=False,
            )
            st.plotly_chart(fig_roll, width="stretch", config={'displayModeBar': True})

    # TAB 3: Return Distributions & Daily Returns Analysis
    with tab_dist:
        st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600; margin-top: 10px; margin-bottom: 15px;'>Daily Returns Analysis</h4>", unsafe_allow_html=True)
        
        returns_df = calculate_daily_returns(nav_df).dropna(subset=["daily_return_pct"])
        
        if not returns_df.empty:
            ret_stats = daily_return_statistics(returns_df)
            
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                st.markdown(
                    render_return_kpi_card(
                        "Best Daily Return (%)", 
                        f"+{ret_stats['best_pct']:.2f}%", 
                        f"Occurred on {ret_stats['best_date']}", 
                        "#10B981", 
                        ""
                    ),
                    unsafe_allow_html=True
                )
            with rc2:
                st.markdown(
                    render_return_kpi_card(
                        "Worst Daily Return (%)", 
                        f"{ret_stats['worst_pct']:.2f}%", 
                        f"Occurred on {ret_stats['worst_date']}", 
                        "#EF4444", 
                        ""
                    ),
                    unsafe_allow_html=True
                )
            with rc3:
                st.markdown(
                    render_return_kpi_card(
                        "Average Daily Return (%)", 
                        f"{ret_stats['avg_pct']:.3f}%", 
                        "Mean daily change", 
                        "#3B82F6", 
                        ""
                    ),
                    unsafe_allow_html=True
                )
                
            st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Daily Returns Over Time</h5>", unsafe_allow_html=True)
                fig_time = go.Figure()
                fig_time.add_trace(
                    go.Scatter(
                        x=returns_df["full_date"],
                        y=returns_df["daily_return_pct"],
                        mode="lines",
                        name="Daily Return",
                        line=dict(
                            color="#3B82F6",
                            width=1.5
                        ),
                        hovertemplate="<b>%{x|%d %b %Y}</b><br>Daily Return: %{y:.2f}%<extra></extra>"
                    )
                )
                fig_time.update_layout(
                    template="plotly_white",
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font_family="Inter, sans-serif",
                    font_color="#0C1E36",
                    height=350,
                    margin=dict(l=40, r=20, t=10, b=40),
                    hovermode="x unified",
                    xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
                    yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Daily Return (%)"),
                    showlegend=False,
                )
                st.plotly_chart(fig_time, width="stretch", config={'displayModeBar': False})
                
            with col_chart2:
                st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Return Distribution (Histogram)</h5>", unsafe_allow_html=True)
                
                mean_ret = returns_df["daily_return_pct"].mean()
                median_ret = returns_df["daily_return_pct"].median()
                
                fig_dist = px.histogram(
                    returns_df,
                    x="daily_return_pct",
                    nbins=40,
                    labels={"daily_return_pct": "Daily Return (%)"},
                )
                
                fig_dist.update_traces(
                    marker_color="#2E3192",
                    opacity=0.85,
                    hovertemplate="<b>Daily Return Range</b>: %{x}%<br><b>Frequency</b>: %{y}<extra></extra>"
                )
                
                fig_dist.add_vline(x=mean_ret, line_dash="dash", line_color="#F58220", line_width=2)
                fig_dist.add_vline(x=median_ret, line_dash="dot", line_color="#0C1E36", line_width=2)
                
                fig_dist.update_layout(
                    template="plotly_white",
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font_family="Inter, sans-serif",
                    font_color="#0C1E36",
                    height=350,
                    margin=dict(l=40, r=20, t=10, b=40),
                    xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
                    yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Frequency"),
                    annotations=[
                        dict(x=mean_ret, y=0.95, yref="paper", text=f"Mean: {mean_ret:.3f}%", showarrow=False, font=dict(color="#F58220", size=10), bgcolor="white"),
                        dict(x=median_ret, y=0.85, yref="paper", text=f"Median: {median_ret:.3f}%", showarrow=False, font=dict(color="#0C1E36", size=10), bgcolor="white")
                    ]
                )
                st.plotly_chart(fig_dist, width="stretch", config={'displayModeBar': False})
        else:
            st.warning("⚠️ Not enough daily returns data points to calculate returns analysis.")

    # TAB 4: Risk & Drawdown
    with tab_drawdown:
        st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600; margin-top: 10px; margin-bottom: 5px;'>Historical Drawdowns</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #64748B; margin-top: 0; margin-bottom: 20px;'>Drawdown represents the peak-to-trough decline of the fund's NAV relative to its running maximum. This displays the severity and recovery timeline of market losses.</p>", unsafe_allow_html=True)
        
        dd_stats = get_drawdown_statistics(drawdown_precomputed)
        
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        dcol1, dcol2, dcol3, dcol4, dcol5 = st.columns(5)
        
        with dcol1:
            curr_dd_color = "#10B981" if dd_stats["current_drawdown"] >= 0 else "#EF4444"
            st.markdown(
                render_return_kpi_card(
                    "Current Drawdown (%)",
                    f"{dd_stats['current_drawdown']:.2f}%",
                    f"As of {latest_date}",
                    curr_dd_color,
                    ""
                ),
                unsafe_allow_html=True
            )
        with dcol2:
            st.markdown(
                render_return_kpi_card(
                    "Maximum Drawdown (%)",
                    f"{dd_stats['max_drawdown']:.2f}%",
                    f"Trough on {dd_stats['max_dd_date']}",
                    "#991B1B",
                    ""
                ),
                unsafe_allow_html=True
            )
        with dcol3:
            st.markdown(
                render_return_kpi_card(
                    "Peak NAV (₹)",
                    f"₹ {dd_stats['highest_nav']:.2f}",
                    f"Peak on {dd_stats['highest_nav_date']}",
                    "#2E3192",
                    ""
                ),
                unsafe_allow_html=True
            )
        with dcol4:
            status_val = "At Peak" if dd_stats["is_recovering"] else "In Trough"
            status_sub = "All-time high achieved" if dd_stats["is_recovering"] else f"In drawdown for {dd_stats['days_in_drawdown']} trading days"
            status_color = "#10B981" if dd_stats["is_recovering"] else "#F58220"
            st.markdown(
                render_return_kpi_card(
                    "Drawdown Status",
                    status_val,
                    status_sub,
                    status_color,
                    "⏳"
                ),
                unsafe_allow_html=True
            )
        with dcol5:
            rec_color = "#64748B" if dd_stats["recovery_needed_pct"] == 0 else "#8B5CF6"
            st.markdown(
                render_return_kpi_card(
                    "Recovery Needed (%)",
                    f"+{dd_stats['recovery_needed_pct']:.2f}%",
                    "To reach previous peak",
                    rec_color,
                    ""
                ),
                unsafe_allow_html=True
            )
            
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
        
        fig_dd = go.Figure()
        fig_dd.add_trace(
            go.Scatter(
                x=drawdown_precomputed["full_date"],
                y=drawdown_precomputed["drawdown_pct"],
                mode="lines",
                name="Drawdown",
                line=dict(
                    color="#EF4444", 
                    width=2
                ),
                fill="tozeroy",
                fillcolor="rgba(239, 68, 68, 0.15)",
                customdata=drawdown_precomputed["peak_nav"],
                hovertemplate="<b>%{x|%d %b %Y}</b><br>Drawdown: %{y:.2f}%<br>Peak NAV: ₹%{customdata:.2f}<extra></extra>"
            )
        )
        fig_dd.update_layout(
            template="plotly_white",
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_family='Inter, sans-serif',
            font_color='#0C1E36',
            height=400,
            margin=dict(l=40, r=20, t=15, b=40),
            hovermode="x unified",
            xaxis=dict(
                showgrid=False, 
                linecolor='#E2E8F0',
                title=dict(text="Date", font=dict(size=12, color='#64748B'))
            ),
            yaxis=dict(
                showgrid=True, 
                gridcolor='#F1F5F9', 
                linecolor='#E2E8F0',
                title=dict(text="Drawdown (%)", font=dict(size=12, color='#64748B'))
            ),
            showlegend=False,
        )
        st.plotly_chart(fig_dd, width="stretch", config={'displayModeBar': True})
        
        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 15px; margin-top: 15px;">
                <div style="font-family: 'Inter', sans-serif; font-size: 13px; color: #475569; line-height: 1.5;">
                    ℹ️ <strong>Drawdown Analysis Insight:</strong> Drawdown is a measure of downside risk. The maximum drawdown of <strong>{dd_stats['max_drawdown']:.2f}%</strong> occurred on <strong>{dd_stats['max_dd_date']}</strong>. 
                    {"The fund has recovered and is currently trading at its peak." if dd_stats['is_recovering'] else f"Currently, the fund is in a drawdown of <strong>{dd_stats['current_drawdown']:.2f}%</strong>, which has lasted for <strong>{dd_stats['days_in_drawdown']}</strong> consecutive trading days. It requires a return of <strong>+{dd_stats['recovery_needed_pct']:.2f}%</strong> from the current NAV of ₹{drawdown_precomputed['nav'].iloc[-1]:.2f} to regain its previous peak of ₹{dd_stats['highest_nav']:.2f}."}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # TAB 5: Monthly NAV Analysis
    with tab_monthly:
        st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600; margin-top: 10px; margin-bottom: 5px;'>Monthly NAV Analysis</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #64748B; margin-top: 0; margin-bottom: 20px;'>Aggregated monthly averages and Month-over-Month (MoM) point-to-point performance returns.</p>", unsafe_allow_html=True)
        
        monthly_df = monthly_nav(nav_df)
        monthly_returns = calculate_monthly_returns(nav_df)
        m_stats = get_monthly_return_statistics(monthly_returns)
        
        mcol1, mcol2, mcol3 = st.columns(3)
        with mcol1:
            st.markdown(
                render_return_kpi_card(
                    "Best Performing Month (%)",
                    f"+{m_stats['best_pct']:.2f}%",
                    f"Achieved in {m_stats['best_month']}",
                    "#10B981", 
                    ""
                ),
                unsafe_allow_html=True
            )
        with mcol2:
            st.markdown(
                render_return_kpi_card(
                    "Worst Performing Month (%)",
                    f"{m_stats['worst_pct']:.2f}%",
                    f"Occurred in {m_stats['worst_month']}",
                    "#EF4444", 
                    ""
                ),
                unsafe_allow_html=True
            )
        with mcol3:
            st.markdown(
                render_return_kpi_card(
                    "Monthly Consistency",
                    m_stats['profitable_ratio'],
                    "Profitable vs Total Months",
                    "#3B82F6", 
                    ""
                ),
                unsafe_allow_html=True
            )
            
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
        
        m_chart1, m_chart2 = st.columns(2)
        
        with m_chart1:
            st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Monthly Average NAV Trend</h5>", unsafe_allow_html=True)
            fig_month = go.Figure()
            fig_month.add_trace(
                go.Bar(
                    x=monthly_df["month"],
                    y=monthly_df["nav"],
                    marker_color="#2E3192",
                    opacity=0.9,
                    hovertemplate="<b>Month</b>: %{x}<br>Average NAV: ₹%{y:.2f}<extra></extra>"
                )
            )
            fig_month.update_layout(
                template="plotly_white",
                plot_bgcolor='white',
                paper_bgcolor='white',
                font_family='Inter, sans-serif',
                font_color='#0C1E36',
                height=350,
                margin=dict(l=40, r=20, t=10, b=40),
                hovermode="x unified",
                xaxis=dict(
                    showgrid=False, 
                    linecolor='#E2E8F0',
                    title=dict(text="Month", font=dict(size=12, color='#64748B'))
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='#F1F5F9', 
                    linecolor='#E2E8F0',
                    title=dict(text="Average NAV (₹)", font=dict(size=12, color='#64748B'))
                ),
                showlegend=False,
            )
            st.plotly_chart(fig_month, width="stretch", config={'displayModeBar': False})
            
        with m_chart2:
            st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Month-over-Month (MoM) Returns</h5>", unsafe_allow_html=True)
            
            bar_colors = ["#10B981" if val >= 0 else "#EF4444" for val in monthly_returns["monthly_return_pct"]]
            
            fig_m_ret = go.Figure()
            fig_m_ret.add_trace(
                go.Bar(
                    x=monthly_returns["month_str"],
                    y=monthly_returns["monthly_return_pct"],
                    marker_color=bar_colors,
                    opacity=0.9,
                    hovertemplate="<b>Month</b>: %{x}<br>Return: %{y:.2f}%<extra></extra>"
                )
            )
            fig_m_ret.update_layout(
                template="plotly_white",
                plot_bgcolor='white',
                paper_bgcolor='white',
                font_family='Inter, sans-serif',
                font_color='#0C1E36',
                height=350,
                margin=dict(l=40, r=20, t=10, b=40),
                hovermode="x unified",
                xaxis=dict(
                    showgrid=False, 
                    linecolor='#E2E8F0',
                    title=dict(text="Month", font=dict(size=12, color='#64748B'))
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='#F1F5F9', 
                    linecolor='#E2E8F0',
                    title=dict(text="Return (%)", font=dict(size=12, color='#64748B'))
                ),
                showlegend=False,
            )
            st.plotly_chart(fig_m_ret, width="stretch", config={'displayModeBar': False})

    # TAB 6: Statistics & Insights
    with tab_stats:
        st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600; margin-top: 10px; margin-bottom: 15px;'>Statistical Breakdown & Analysis</h4>", unsafe_allow_html=True)
        
        col_table, col_insights = st.columns([1, 1])
        insights = generate_dynamic_insights(nav_df)
        
        with col_table:
            stats_display = pd.DataFrame({
                "Statistical Parameter": [
                    "Analysis Date Range",
                    "Latest NAV (₹)",
                    "Highest NAV (₹)",
                    "Lowest NAV (₹)",
                    "Average NAV (₹)",
                    "Median NAV (₹)",
                    "Standard Deviation (₹)",
                    "Annualized Volatility (%)",
                    "Observations count (Count)"
                ],
                "Value": [
                    f"{stats['start_date']} to {stats['end_date']}",
                    f"₹ {stats['latest']:.4f}",
                    f"₹ {stats['highest']:.4f}",
                    f"₹ {stats['lowest']:.4f}",
                    f"₹ {stats['average']:.4f}",
                    f"₹ {stats['median']:.4f}",
                    f"₹ {stats['std']:.4f}",
                    f"{stats['volatility']:.2f}%",
                    f"{stats['observations']:,}"
                ]
            })
            st.dataframe(stats_display, width="stretch", hide_index=True)
            
        with col_insights:
            volatility_class = "Moderate"
            if stats['volatility'] < 8.0:
                volatility_class = "Low"
            elif stats['volatility'] > 18.0:
                volatility_class = "High"
                
            st.markdown(
                f"""
                <div class="fc-card" style="padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%; margin-bottom: 0px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-family: 'Inter', sans-serif;">
                        <span style="font-size: 20px; line-height: 1;"></span>
                        <span style="font-weight: 700; color: #2E3192; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Executive Insights</span>
                    </div>
                    <ul style="font-size: 13px; color: #475569; line-height: 1.6; padding-left: 20px; margin: 0; font-family: 'Inter', sans-serif;">
                        <li style="margin-bottom: 8px;">
                            <strong>Peak Performance:</strong> Highest NAV of <strong>₹ {insights['highest_nav']:.2f}</strong> was reached on <strong>{insights['highest_nav_date']}</strong>.
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Lowest Point:</strong> Lowest NAV of <strong>₹ {insights['lowest_nav']:.2f}</strong> occurred on <strong>{insights['lowest_nav_date']}</strong>.
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Overall Return:</strong> The fund NAV has generated a cumulative change of <strong>{insights['total_return']:.2f}%</strong> over the analysis period.
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Current Trend:</strong> The short-term movement is currently classified as <strong>{insights['trend']}</strong>.
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Risk profile:</strong> Annualized Volatility is <strong>{stats['volatility']:.2f}%</strong> ({volatility_class} Volatility Class) with a Maximum Drawdown of <strong>{insights['max_drawdown']:.2f}%</strong> on <strong>{insights['max_dd_date']}</strong>.
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Daily Return:</strong> The average daily return has been <strong>{insights['avg_daily_return']:.3f}%</strong>.
                        </li>
                        <li style="margin-bottom: 0px;">
                            <strong>Monthly Consistency:</strong> Out of {len(monthly_returns)} completed months, the fund was profitable in <strong>{insights['profitable_ratio']}</strong> months. The best month was <strong>{insights['best_month']} (+{insights['best_month_pct']:.2f}%)</strong> and the worst month was <strong>{insights['worst_month']} ({insights['worst_month_pct']:.2f}%)</strong>.
                        </li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )


if __name__ == "__main__":
    render_layout("NAV Analytics", show)