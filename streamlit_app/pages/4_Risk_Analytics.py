"""Risk Analytics page."""
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
from streamlit_app.helpers import clean_html
from streamlit_app.services.risk_service import (
    load_risk_data,
    get_filter_options,
    filter_risk_data,
    calculate_risk_summary_statistics,
    generate_risk_insights,
)

def render_return_kpi_card(title: str, value: str, subtitle: str, color: str, icon: str) -> str:
    """Generate HTML for styled return metric card."""
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
    """Render the Risk Analytics dashboard."""
    st.markdown(
        """
        <h2 style="color:#0C1E36;margin-bottom:5px;">
            Risk Analytics
        </h2>
        <p style="color:#64748B;font-size:16px;">
            Evaluate and compare mutual fund risk profiles, standard deviation distributions, and risk-adjusted ratios
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    raw_df = load_risk_data()
    filter_opts = get_filter_options(raw_df)
    
    st.markdown(
        "<span style='color: #64748B; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;'>Risk filter control deck</span>", 
        unsafe_allow_html=True
    )
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        selected_houses = st.multiselect(
            "Fund House:",
            options=filter_opts["fund_houses"],
            placeholder="All Fund Houses",
            key="risk_house_filter"
        )
    with col_f2:
        selected_categories = st.multiselect(
            "Category:",
            options=filter_opts["categories"],
            placeholder="All Categories",
            key="risk_cat_filter"
        )
    with col_f3:
        selected_plans = st.multiselect(
            "Plan Type:",
            options=filter_opts["plans"],
            placeholder="All Plans",
            key="risk_plan_filter"
        )
    with col_f4:
        selected_risks = st.multiselect(
            "Risk Category:",
            options=filter_opts["risk_categories"],
            placeholder="All Risk Levels",
            key="risk_level_filter"
        )
        
    df_filtered = filter_risk_data(
        raw_df,
        fund_houses=selected_houses,
        categories=selected_categories,
        plans=selected_plans,
        risk_categories=selected_risks
    )
    
    if df_filtered.empty:
        st.warning("⚠️ No mutual funds match the selected filter criteria. Please adjust your filters.")
        return
        
    stats = calculate_risk_summary_statistics(df_filtered)
    
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    # Row 1 of KPI Cards
    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1:
        st.markdown(
            render_return_kpi_card(
                "Avg Std Deviation (%)",
                f"{stats['avg_std_dev']:.2f}%",
                "Annualized volatility proxy",
                "#2E3192",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol2:
        st.markdown(
            render_return_kpi_card(
                "Avg Sharpe Ratio",
                f"{stats['avg_sharpe']:.2f}",
                "Risk-adjusted excess return",
                "#3B82F6",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol3:
        st.markdown(
            render_return_kpi_card(
                "Avg Alpha (%)",
                f"{stats['avg_alpha']:.2f}%",
                "Performance above benchmark",
                "#10B981",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol4:
        st.markdown(
            render_return_kpi_card(
                "Avg Beta",
                f"{stats['avg_beta']:.2f}",
                "Systematic market risk factor",
                "#64748B",
                ""
            ),
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    
    # Row 2 of KPI Cards
    kcol5, kcol6, kcol7, kcol_obs = st.columns(4)
    with kcol5:
        st.markdown(
            render_return_kpi_card(
                "Avg Volatility (%)",
                f"{stats['avg_volatility']:.2f}%",
                "Average deviation factor",
                "#F58220",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol6:
        st.markdown(
            render_return_kpi_card(
                "Avg Sortino Ratio",
                f"{stats['avg_sortino']:.2f}",
                "Downside deviation risk ratio",
                "#8B5CF6",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol7:
        st.markdown(
            render_return_kpi_card(
                "Avg Max Drawdown (%)",
                f"{stats['avg_max_drawdown']:.2f}%",
                "Mean historical correction depth",
                "#EF4444",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol_obs:
        st.markdown(
            render_return_kpi_card(
                "Filtered Universe",
                f"{stats['observations']:,} Funds",
                "Schemes matching filters",
                "#0F172A",
                ""
            ),
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    
    col_plot, col_insights = st.columns([2, 1])
    
    with col_plot:
        scatter_df = df_filtered.dropna(subset=["std_dev", "return_3yr_pct"]).copy()
        scatter_df["size_aum"] = scatter_df["aum"].apply(lambda x: max(float(x), 0.1) if not pd.isna(x) else 0.1)
        
        fig_scatter = px.scatter(
            scatter_df,
            x="std_dev",
            y="return_3yr_pct",
            size="size_aum",
            color="category",
            hover_name="scheme_name",
            hover_data={
                "category": True,
                "std_dev": ":.2f%",
                "return_3yr_pct": ":.2f%",
                "aum": ":,.2f Crore",
                "sharpe_ratio": ":.2f"
            },
            labels={
                "std_dev": "Volatility (Standard Deviation %)",
                "return_3yr_pct": "3-Year Return (%)",
                "size_aum": "AUM (₹ Crore)",
                "category": "Category"
            },
            template="plotly_white"
        )
        
        fig_scatter.update_layout(
            title=dict(text="Risk vs Return Profile (3-Year Horizon)", font=dict(size=14, color="#0C1E36", family="Inter, sans-serif")),
            font_family="Inter, sans-serif",
            font_color="#0C1E36",
            height=400,
            margin=dict(l=40, r=20, t=40, b=40),
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0")
        )
        st.plotly_chart(fig_scatter, width="stretch", config={'displayModeBar': False})
        
    with col_insights:
        insights = generate_risk_insights(df_filtered)
        
        st.markdown(
            f"""
            <div class="fc-card" style="padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%; margin-bottom: 0px; min-height: 400px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-family: 'Inter', sans-serif;">
                        <span style="font-size: 20px; line-height: 1;"></span>
                        <span style="font-weight: 700; color: #2E3192; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Risk Insights</span>
                    </div>
                    <ul style="font-size: 12.5px; color: #475569; line-height: 1.5; padding-left: 20px; margin: 0; font-family: 'Inter', sans-serif;">
                        <li style="margin-bottom: 8px;">
                            <strong>Lowest Risk / Most Stable:</strong><br>
                            <span style="color: #2E3192; font-weight: 600;">{insights['lowest_risk_fund']}</span><br>
                            Std Dev: <strong>{insights['lowest_risk_val']:.2f}%</strong>
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Best Risk-Adjusted:</strong><br>
                            <span style="color: #8B5CF6; font-weight: 600;">{insights['best_risk_adj_fund']}</span><br>
                            Sortino Ratio: <strong>{insights['best_risk_adj_val']:.2f}</strong>
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Highest Alpha Gen:</strong><br>
                            <span style="color: #10B981; font-weight: 600;">{insights['highest_alpha_fund']}</span><br>
                            Alpha: <strong>{insights['highest_alpha_val']:.2f}%</strong>
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Highest Market Beta:</strong><br>
                            <span style="color: #64748B; font-weight: 600;">{insights['highest_beta_fund']}</span><br>
                            Beta: <strong>{insights['highest_beta_val']:.2f}</strong>
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Highest Sharpe Ratio:</strong><br>
                            <span style="color: #3B82F6; font-weight: 600;">{insights['highest_sharpe_fund']}</span><br>
                            Sharpe: <strong>{insights['highest_sharpe_val']:.2f}</strong>
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Safest Drawdown Profile:</strong><br>
                            <span style="color: #EF4444; font-weight: 600;">{insights['lowest_dd_fund']}</span><br>
                            Max Drawdown: <strong>{insights['lowest_dd_val']:.2f}%</strong>
                        </li>
                        <li style="margin-bottom: 0px;">
                            <strong>Highest Volatility:</strong><br>
                            <span style="color: #F58220; font-weight: 600;">{insights['highest_vol_fund']}</span><br>
                            Std Dev: <strong>{insights['highest_vol_val']:.2f}%</strong>
                        </li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    
    col_dist_chart, col_sharpe_tables = st.columns(2)
    
    with col_dist_chart:
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Volatility Distribution (Histogram)</h5>", unsafe_allow_html=True)
        
        mean_vol = df_filtered["std_dev"].mean()
        median_vol = df_filtered["std_dev"].median()
        
        fig_dist = px.histogram(
            df_filtered,
            x="std_dev",
            nbins=20,
            labels={"std_dev": "Volatility (Standard Deviation %)"},
            template="plotly_white"
        )
        
        fig_dist.update_traces(
            marker_color="#2E3192",
            opacity=0.85,
            hovertemplate="<b>Vol Range</b>: %{x}%<br><b>Fund Count</b>: %{y}<extra></extra>"
        )
        
        fig_dist.add_vline(x=mean_vol, line_dash="dash", line_color="#F58220", line_width=2)
        fig_dist.add_vline(x=median_vol, line_dash="dot", line_color="#0C1E36", line_width=2)
        
        fig_dist.update_layout(
            font_family="Inter, sans-serif",
            font_color="#0C1E36",
            height=350,
            margin=dict(l=40, r=20, t=10, b=40),
            xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Count"),
            annotations=[
                dict(x=mean_vol, y=0.95, yref="paper", text=f"Mean: {mean_vol:.2f}%", showarrow=False, font=dict(color="#F58220", size=10), bgcolor="white"),
                dict(x=median_vol, y=0.85, yref="paper", text=f"Median: {median_vol:.2f}%", showarrow=False, font=dict(color="#0C1E36", size=10), bgcolor="white")
            ]
        )
        st.plotly_chart(fig_dist, width="stretch", config={'displayModeBar': False})
        
    with col_sharpe_tables:
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Risk-Adjusted Leaders & Laggards</h5>", unsafe_allow_html=True)
        
        sharpe_sorted = df_filtered.dropna(subset=["sharpe_ratio"]).sort_values("sharpe_ratio", ascending=False)
        top_5 = sharpe_sorted.head(5)[["scheme_name", "sharpe_ratio"]].rename(columns={"scheme_name": "Scheme Name", "sharpe_ratio": "Sharpe Ratio"})
        bottom_5 = sharpe_sorted.tail(5)[["scheme_name", "sharpe_ratio"]].sort_values("sharpe_ratio", ascending=True).rename(columns={"scheme_name": "Scheme Name", "sharpe_ratio": "Sharpe Ratio"})
        
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.markdown("<span style='font-size: 11px; font-weight:600; color:#10B981;'>Top 5 Sharpe Ratio</span>", unsafe_allow_html=True)
            st.dataframe(top_5, width="stretch", hide_index=True)
        with t_col2:
            st.markdown("<span style='font-size: 11px; font-weight:600; color:#EF4444;'>Bottom 5 Sharpe Ratio</span>", unsafe_allow_html=True)
            st.dataframe(bottom_5, width="stretch", hide_index=True)
            
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600;'>Risk Score Dashboard</h4>", unsafe_allow_html=True)
    
    table_display = df_filtered[[
        "scheme_name", "fund_house", "category", "plan", "return_3yr_pct", "std_dev",
        "sharpe_ratio", "sortino_ratio", "alpha", "beta", "max_drawdown", "expense_ratio", "aum"
    ]].rename(columns={
        "scheme_name": "Fund Name",
        "fund_house": "Fund House",
        "category": "Category",
        "plan": "Plan",
        "return_3yr_pct": "Return 3Y (%)",
        "std_dev": "Volatility (%)",
        "sharpe_ratio": "Sharpe Ratio",
        "sortino_ratio": "Sortino Ratio",
        "alpha": "Alpha (%)",
        "beta": "Beta",
        "max_drawdown": "Maximum Drawdown (%)",
        "expense_ratio": "Expense Ratio (%)",
        "aum": "AUM (₹ Crore)"
    })
    
    st.dataframe(table_display, width="stretch", hide_index=True)


if __name__ == "__main__":
    render_layout("Risk Analytics", show)
