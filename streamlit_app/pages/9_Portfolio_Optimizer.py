"""Portfolio Optimizer page."""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from streamlit_app.components.layout import render_layout
from streamlit_app.database import get_db_connection
from streamlit_app.helpers import clean_html
from streamlit_app.services.optimizer_service import (
    optimize_portfolio,
    calculate_custom_portfolio
)
from streamlit_app.services.report_service import export_to_csv

def render_return_kpi_card(title: str, value: str, subtitle: str, color: str, icon: str) -> str:
    """Generate HTML for styled return metric card."""
    html_content = f"""
    <div class="fc-card" style="padding: 16px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 90px; height: 100%; margin-bottom: 0px; border-left: 4px solid {color};">
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
    """Render the Portfolio Optimizer page content."""
    st.markdown(
        """
        <h2 style="color:#0C1E36;margin-bottom:5px;">
            Portfolio Optimizer
        </h2>
        <p style="color:#64748B;font-size:16px;">
            Construct optimized assets weights using Markowitz Modern Portfolio Theory (MPT) and Efficient Frontiers
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("<hr style='margin-top: 15px; margin-bottom: 25px; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    df_funds = pd.read_sql_query("SELECT fund_id, scheme_name FROM dim_fund", conn)
    conn.close()
    
    if df_funds.empty:
        st.warning("⚠️ No mutual fund options found in database.")
        return
        
    st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase; margin-bottom: 10px;'>Portfolio optimization controls</h5>", unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    
    with col_f1:
        default_selections = df_funds["scheme_name"].head(4).tolist()
        selected_funds = st.multiselect(
            "Select Funds (2 to 5):",
            options=df_funds["scheme_name"].tolist(),
            default=default_selections,
            max_selections=5,
            key="opt_funds_multiselect"
        )
    with col_f2:
        rf_rate = st.slider(
            "Risk-Free Rate (%):",
            min_value=2.0,
            max_value=10.0,
            value=6.0,
            step=0.1,
            key="opt_rf_rate"
        )
    with col_f3:
        num_simulations = st.slider(
            "Portfolios to Simulate:",
            min_value=1000,
            max_value=4000,
            value=2000,
            step=500,
            key="opt_sim_count"
        )
        
    if len(selected_funds) < 2:
        st.info("Please select at least 2 mutual funds to begin portfolio optimization analysis.")
        return
        
    selected_ids = []
    for name in selected_funds:
        fid = int(df_funds[df_funds["scheme_name"] == name]["fund_id"].iloc[0])
        selected_ids.append(fid)
        
    results = optimize_portfolio(
        selected_ids,
        selected_funds,
        num_portfolios=num_simulations,
        rf_rate=rf_rate,
        seed=42
    )
    
    if not results:
        st.warning("⚠️ Selected funds have non-overlapping daily NAV timelines. Please select another set of funds.")
        return
        
    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Customize Weight allocation (%)</h5>", unsafe_allow_html=True)
    
    col_w = st.columns(len(selected_funds))
    custom_weights = []
    
    equal_weight = 100.0 / len(selected_funds)
    
    for idx, fund in enumerate(selected_funds):
        with col_w[idx]:
            short_name = fund[:20] + ".." if len(fund) > 22 else fund
            w = st.number_input(
                f"{short_name}:",
                min_value=0.0,
                max_value=100.0,
                value=float(round(equal_weight, 2)),
                step=1.0,
                key=f"opt_weight_{idx}"
            )
            custom_weights.append(w)
            
    weight_sum = sum(custom_weights)
    if not (99.9 <= weight_sum <= 100.1):
        st.error(f"❌ Allocation weights must sum to exactly **100%** (current sum: **{weight_sum:.2f}%**). Adjust the inputs above.")
        
    expected_returns_vector = [results["funds_expected_returns"][f] for f in selected_funds]
    custom_stats = calculate_custom_portfolio(
        custom_weights,
        expected_returns_vector,
        results["ann_cov_matrix"],
        rf_rate=rf_rate
    )
    
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1:
        st.markdown(
            render_return_kpi_card(
                "Max Sharpe Return (%)",
                f"{results['max_sharpe_return']:.2f}%",
                f"Volatility: {results['max_sharpe_vol']:.2f}%",
                "#2E3192",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol2:
        st.markdown(
            render_return_kpi_card(
                "Max Sharpe Ratio",
                f"{results['max_sharpe_val']:.2f}",
                "Best risk-adjusted option",
                "#F58220",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol3:
        st.markdown(
            render_return_kpi_card(
                "Min Volatility Return (%)",
                f"{results['min_vol_return']:.2f}%",
                f"Volatility: {results['min_vol_vol']:.2f}%",
                "#10B981",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol4:
        st.markdown(
            render_return_kpi_card(
                "Custom Return (%)",
                f"{custom_stats['return_pct']:.2f}%" if (99.9 <= weight_sum <= 100.1) else "N/A",
                f"Vol: {custom_stats['vol_pct']:.2f}% | SR: {custom_stats['sharpe']:.2f}" if (99.9 <= weight_sum <= 100.1) else "Check allocation sums",
                "#3B82F6",
                ""
            ),
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    col_chart, col_alloc = st.columns([2, 1])
    
    with col_chart:
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Markowitz Efficient Frontier</h5>", unsafe_allow_html=True)
        
        fig = go.Figure()
        
        vol_display = results["portfolio_vol"] * 100.0
        ret_display = results["portfolio_ret"] * 100.0
        
        fig.add_trace(
            go.Scatter(
                x=vol_display,
                y=ret_display,
                mode="markers",
                marker=dict(
                    color=results["portfolio_sharpe"],
                    colorscale="Blues",
                    showscale=True,
                    colorbar=dict(
                        title="Sharpe Ratio", 
                        thickness=15, 
                        len=0.75,
                        x=1.05,
                        y=0.5,
                        yanchor="middle"
                    ),
                    size=4,
                    opacity=0.6
                ),
                name="Simulated Portfolios",
                hovertemplate="Risk (Vol): %{x:.2f}%<br>Return: %{y:.2f}%<br>Sharpe: %{marker.color:.2f}<extra></extra>"
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=[results["max_sharpe_vol"]],
                y=[results["max_sharpe_return"]],
                mode="markers",
                marker=dict(
                    color="#EF4444", 
                    size=14, 
                    symbol="star", 
                    line=dict(color="black", width=1.5)
                ),
                name="Maximum Sharpe Portfolio"
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=[results["min_vol_vol"]],
                y=[results["min_vol_return"]],
                mode="markers",
                marker=dict(
                    color="#10B981", 
                    size=12, 
                    symbol="diamond", 
                    line=dict(color="black", width=1.5)
                ),
                name="Minimum Variance Portfolio"
            )
        )
        
        if 99.9 <= weight_sum <= 100.1:
            fig.add_trace(
                go.Scatter(
                    x=[custom_stats["vol_pct"]],
                    y=[custom_stats["return_pct"]],
                    mode="markers",
                    marker=dict(
                        color="#F58220", 
                        size=12, 
                        symbol="circle", 
                        line=dict(color="black", width=1.5)
                    ),
                    name="Custom Portfolio"
                )
            )
            
        fig.update_layout(
            template="plotly_white",
            font_family="Inter, sans-serif",
            font_color="#0C1E36",
            height=420,
            margin=dict(l=55, r=85, t=15, b=95),
            xaxis=dict(
                title="Portfolio Risk / Volatility (%)", 
                showgrid=True, 
                gridcolor="#F1F5F9", 
                linecolor="#E2E8F0"
            ),
            yaxis=dict(
                title="Annualized Expected Return (%)", 
                showgrid=True, 
                gridcolor="#F1F5F9", 
                linecolor="#E2E8F0"
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.25,
                xanchor="center",
                x=0.5,
                font=dict(size=10.5),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#E2E8F0",
                borderwidth=1
            )
        )
        st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})
        
    with col_alloc:
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Allocation Comparison</h5>", unsafe_allow_html=True)
        
        alloc_data = []
        for fund in selected_funds:
            alloc_data.append({
                "Fund": fund,
                "Max Sharpe (%)": f"{results['max_sharpe_alloc'][fund]:.2f}%",
                "Min Volatility (%)": f"{results['min_vol_alloc'][fund]:.2f}%"
            })
        df_alloc = pd.DataFrame(alloc_data)
        
        st.dataframe(df_alloc, width="stretch", hide_index=True)
        
        csv_bytes = export_to_csv(df_alloc)
        st.download_button(
            label="Download Weights (CSV)",
            data=csv_bytes,
            file_name="mpt_allocations.csv",
            mime="text/csv",
            key="btn_mpt_csv_download",
            width="stretch"
        )
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600;'>Fund Return Profiles</h4>", unsafe_allow_html=True)
    
    fund_profiles = []
    for fund in selected_funds:
        fund_profiles.append({
            "Mutual Fund": fund,
            "Annualized Expected Return (%)": f"{results['funds_expected_returns'][fund]:.2f}%"
        })
    df_profiles = pd.DataFrame(fund_profiles)
    st.dataframe(df_profiles.sort_values("Annualized Expected Return (%)", ascending=False), width="stretch", hide_index=True)


if __name__ == "__main__":
    render_layout("Portfolio Optimizer", show)
