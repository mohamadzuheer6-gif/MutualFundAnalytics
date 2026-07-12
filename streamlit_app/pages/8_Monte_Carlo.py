"""Monte Carlo Simulation page."""
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
from streamlit_app.services.monte_carlo_service import simulate_monte_carlo, generate_mc_insights

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
    """Render the Monte Carlo simulation page content."""
    st.markdown(
        """
        <h2 style="color:#0C1E36;margin-bottom:5px;">
            Monte Carlo Simulation
        </h2>
        <p style="color:#64748B;font-size:16px;">
            Project future NAV growth and model distribution outcomes over a multi-year horizon
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
        
    st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase; margin-bottom: 10px;'>Simulation Parameter controls</h5>", unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        selected_fund_name = st.selectbox(
            "Select Fund to Model:",
            options=df_funds["scheme_name"].tolist(),
            index=0,
            key="mc_fund_select"
        )
        selected_fund_id = int(df_funds[df_funds["scheme_name"] == selected_fund_name]["fund_id"].iloc[0])
    with col_p2:
        num_simulations = st.slider(
            "Number of Simulated Paths:",
            min_value=500,
            max_value=3000,
            value=1000,
            step=100,
            key="mc_num_paths"
        )
    with col_p3:
        horizon_years = st.slider(
            "Horizon Period (Years):",
            min_value=1,
            max_value=10,
            value=5,
            step=1,
            key="mc_horizon_yrs"
        )
        
    results = simulate_monte_carlo(
        selected_fund_id,
        horizon_years=horizon_years,
        num_paths=num_simulations,
        seed=101
    )
    
    if not results:
        st.warning("⚠️ Insufficient historical NAV data to calculate drift and volatility for this fund.")
        return
        
    insights = generate_mc_insights(results)
    
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1:
        st.markdown(
            render_return_kpi_card(
                "Starting NAV (₹)",
                f"₹{results['start_price']:,.4f}",
                "Latest recorded historical NAV",
                "#2E3192",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol2:
        st.markdown(
            render_return_kpi_card(
                "Mean Projected NAV (₹)",
                f"₹{results['mean_final']:,.4f}",
                f"Expected value at Year {horizon_years}",
                "#F58220",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol3:
        st.markdown(
            render_return_kpi_card(
                "Expected Growth (%)",
                f"{insights['expected_growth_pct']:.2f}%",
                "Projected growth from start price",
                "#10B981",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol4:
        st.markdown(
            render_return_kpi_card(
                "Prob of Gain (%)",
                f"{results['prob_positive']:.2f}%",
                "Likelihood of positive return",
                "#3B82F6",
                ""
            ),
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    col_chart, col_insights = st.columns([2, 1])
    
    with col_chart:
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Projected Wealth Trajectories & Confidence Bands</h5>", unsafe_allow_html=True)
        
        fig = go.Figure()
        
        prices_matrix = results["prices"]
        dates = results["dates"]
        num_sample_paths = min(15, num_simulations)
        
        for p in range(num_sample_paths):
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=prices_matrix[:, p],
                    mode="lines",
                    line=dict(width=0.7, color="#E2E8F0"),
                    hoverinfo="none",
                    showlegend=False
                )
            )
            
        mean_path = np.mean(prices_matrix, axis=1)
        p5_path = np.percentile(prices_matrix, 5, axis=1)
        p95_path = np.percentile(prices_matrix, 95, axis=1)
        
        fig.add_trace(
            go.Scatter(
                x=dates + dates[::-1],
                y=list(p95_path) + list(p5_path)[::-1],
                fill="toself",
                fillcolor="rgba(245, 130, 32, 0.08)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="none",
                name="95% Confidence Band"
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=p5_path,
                name="5th Percentile (Downside Bound)",
                line=dict(color="#EF4444", width=1.5, dash="dash"),
                hovertemplate="<b>Date</b>: %{x}<br>5th Percentile: ₹%{y:,.4f}<extra></extra>"
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=mean_path,
                name="Mean Projected Trend",
                line=dict(color="#2E3192", width=3),
                hovertemplate="<b>Date</b>: %{x}<br>Mean Projected NAV: ₹%{y:,.4f}<extra></extra>"
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=p95_path,
                name="95th Percentile (Upside Bound)",
                line=dict(color="#10B981", width=1.5, dash="dash"),
                hovertemplate="<b>Date</b>: %{x}<br>95th Percentile: ₹%{y:,.4f}<extra></extra>"
            )
        )
        
        fig.update_layout(
            template="plotly_white",
            font_family="Inter, sans-serif",
            font_color="#0C1E36",
            height=380,
            margin=dict(l=40, r=40, t=10, b=40),
            xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
            yaxis=dict(title="NAV (₹)", showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})
        
    with col_insights:
        st.markdown(
            clean_html(f"""
            <div class="fc-card" style="padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%; margin-bottom: 0px; min-height: 380px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 15px; font-family: 'Inter', sans-serif;">
                        <span style="font-size: 20px; line-height: 1;"></span>
                        <span style="font-weight: 700; color: #2E3192; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Simulation Insights</span>
                    </div>
                    <ul style="font-size: 12.5px; color: #475569; line-height: 1.6; padding-left: 20px; margin: 0; font-family: 'Inter', sans-serif;">
                        <li style="margin-bottom: 12px;">
                            <strong>Expected {horizon_years}-Year NAV:</strong><br>
                            The mean simulated trajectory indicates the NAV could reach <span style="color: #2E3192; font-weight: 600;">₹{results['mean_final']:,.4f}</span>, representing a total return of <strong>{insights['expected_growth_pct']:.2f}%</strong>.
                        </li>
                        <li style="margin-bottom: 12px;">
                            <strong>Historical Volatility:</strong><br>
                            Annualized expected volatility is calculated at <strong>{insights['annual_vol_est']:.2f}%</strong> (with a mean historical return of <strong>{insights['annual_return_est']:.2f}%</strong>).
                        </li>
                        <li style="margin-bottom: 12px;">
                            <strong>Downside Bound (95% CI):</strong><br>
                            In 95% of simulated scenarios, the final price remains above the 5th percentile price of <span style="color: #EF4444; font-weight: 600;">₹{results['p5_final']:,.4f}</span>. This sets a maximum expected downside drawdown risk of <strong>{insights['downside_risk_pct']:.2f}%</strong>.
                        </li>
                        <li style="margin-bottom: 0px;">
                            <strong>Probability of Positive Gain:</strong><br>
                            Out of {results['num_paths']:,} randomized paths, <strong>{results['prob_positive']:.2f}%</strong> finished above the starting value.
                        </li>
                    </ul>
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    render_layout("Monte Carlo", show)
