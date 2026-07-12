"""Portfolio Holdings page."""
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
from streamlit_app.services.holdings_service import (
    load_holdings_data,
    get_filter_options,
    filter_holdings_data,
    calculate_holdings_kpis,
    get_top_10_holdings,
    get_sector_allocation,
    get_asset_allocation,
    get_market_cap_allocation,
    generate_holdings_insights,
)

def render_return_kpi_card(title: str, value: str, subtitle: str, color: str, icon: str) -> str:
    """Generate HTML for styled metric card."""
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
    """Render the Portfolio Holdings dashboard."""
    st.markdown(
        """
        <h2 style="color:#0C1E36;margin-bottom:5px;">
            Portfolio Holdings
        </h2>
        <p style="color:#64748B;font-size:16px;">
            Analyze mutual fund portfolio holdings, sector weights, asset class distributions, and market cap allocations
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    raw_df = load_holdings_data()
    filter_opts = get_filter_options(raw_df)
    
    st.markdown(
        "<span style='color: #64748B; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;'>Portfolio filter control deck</span>", 
        unsafe_allow_html=True
    )
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        selected_houses = st.multiselect(
            "Fund House:",
            options=filter_opts["fund_houses"],
            placeholder="All Fund Houses",
            key="hld_house_filter"
        )
    with col_f2:
        selected_schemes = st.multiselect(
            "Scheme Name:",
            options=filter_opts["schemes"],
            placeholder="All Schemes",
            key="hld_scheme_filter"
        )
    with col_f3:
        selected_categories = st.multiselect(
            "Category:",
            options=filter_opts["categories"],
            placeholder="All Categories",
            key="hld_cat_filter"
        )
    with col_f4:
        selected_mcaps = st.multiselect(
            "Market Cap:",
            options=filter_opts["market_caps"],
            placeholder="All Market Caps",
            key="hld_mcap_filter"
        )
        
    df_filtered = filter_holdings_data(
        raw_df,
        fund_houses=selected_houses,
        schemes=selected_schemes,
        categories=selected_categories,
        market_caps=selected_mcaps
    )
    
    if df_filtered.empty:
        st.warning("⚠️ No portfolio holdings match the selected filter criteria. Please adjust your filters.")
        return
        
    kpis = calculate_holdings_kpis(df_filtered)
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1:
        st.markdown(
            render_return_kpi_card(
                "Total Unique Holdings (Count)",
                f"{kpis['total_holdings']:,} Stocks",
                "Distinct stock holdings count",
                "#2E3192",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol2:
        st.markdown(
            render_return_kpi_card(
                "Largest Holding Weight (%)",
                f"{kpis['largest_holding_weight']:.2f}%",
                "Highest allocation percentage",
                "#F58220",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol3:
        st.markdown(
            render_return_kpi_card(
                "Average Holding Weight (%)",
                f"{kpis['avg_holding_weight']:.2f}%",
                "Mean allocation weight of stocks",
                "#10B981",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol4:
        st.markdown(
            render_return_kpi_card(
                "Number of Sectors (Count)",
                f"{kpis['num_sectors']:,} Sectors",
                "Sectors with active allocations",
                "#3B82F6",
                ""
            ),
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    col_bar, col_insights = st.columns([2, 1])
    
    with col_bar:
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Top 10 Portfolio Holdings</h5>", unsafe_allow_html=True)
        top10_df = get_top_10_holdings(df_filtered)
        
        fig_bar = px.bar(
            top10_df,
            x="weight_pct",
            y="stock_name",
            orientation="h",
            labels={"weight_pct": "Allocation Weight (%)", "stock_name": "Stock Name"},
            template="plotly_white"
        )
        fig_bar.update_traces(
            marker_color="#2E3192",
            opacity=0.9,
            hovertemplate="<b>Stock</b>: %{y}<br>Weight: %{x:.2f}%<extra></extra>"
        )
        fig_bar.update_yaxes(categoryorder="total ascending")
        
        fig_bar.update_layout(
            font_family="Inter, sans-serif",
            font_color="#0C1E36",
            height=350,
            margin=dict(l=150, r=20, t=10, b=40),
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0"),
            yaxis=dict(showgrid=False, linecolor="#E2E8F0")
        )
        st.plotly_chart(fig_bar, width="stretch", config={'displayModeBar': False})
        
    with col_insights:
        insights = generate_holdings_insights(df_filtered)
        
        st.markdown(
            f"""
            <div class="fc-card" style="padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%; margin-bottom: 0px; min-height: 350px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 15px; font-family: 'Inter', sans-serif;">
                        <span style="font-size: 20px; line-height: 1;"></span>
                        <span style="font-weight: 700; color: #2E3192; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Portfolio Insights</span>
                    </div>
                    <ul style="font-size: 12.5px; color: #475569; line-height: 1.5; padding-left: 20px; margin: 0; font-family: 'Inter', sans-serif;">
                        <li style="margin-bottom: 10px;">
                            <strong>Largest Portfolio Holding:</strong><br>
                            <span style="color: #2E3192; font-weight: 600;">{insights['largest_holding_name']}</span> (<strong>{insights['largest_holding_val']:.2f}%</strong> weight)
                        </li>
                        <li style="margin-bottom: 10px;">
                            <strong>Most Common Sector:</strong><br>
                            <strong>{insights['most_common_sector']}</strong> sector holds <strong>{insights['most_common_sector_val']:.2f}%</strong> of aggregated assets.
                        </li>
                        <li style="margin-bottom: 10px;">
                            <strong>Largest Market Cap Share:</strong><br>
                            <strong>{insights['largest_market_cap']}</strong> assets capture <strong>{insights['largest_market_cap_val']:.2f}%</strong> allocation share.
                        </li>
                        <li style="margin-bottom: 0px;">
                            <strong>Most Diversified Scheme:</strong><br>
                            <span style="color: #10B981; font-weight: 600;">{insights['most_diversified_fund']}</span> leads with <strong>{insights['most_diversified_count']}</strong> unique stock holdings.
                        </li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    col_sec, col_asset, col_mcap = st.columns(3)
    
    with col_sec:
        with st.container(border=True):
            st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase; margin-bottom: 10px;'>Sector Allocation</h5>", unsafe_allow_html=True)
            sec_df = get_sector_allocation(df_filtered)
            
            if not sec_df.empty and len(sec_df) > 5:
                top_5 = sec_df.head(5).copy()
                others_pct = sec_df.iloc[5:]["percentage"].sum()
                if others_pct > 0:
                    others_row = pd.DataFrame([{"sector": "Others", "percentage": others_pct}])
                    sec_df = pd.concat([top_5, others_row], ignore_index=True)
            
            fig_sec = px.pie(
                sec_df,
                values="percentage",
                names="sector",
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Plotly,
                template="plotly_white"
            )
            fig_sec.update_traces(
                textinfo="percent",
                textposition="inside",
                hovertemplate="<b>Sector</b>: %{label}<br>Weight: %{value:.2f}%<extra></extra>"
            )
            fig_sec.update_layout(
                font_family="Inter, sans-serif",
                font_color="#0C1E36",
                height=360,
                margin=dict(l=10, r=10, t=10, b=90),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.12,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=9.5)
                )
            )
            st.plotly_chart(fig_sec, width="stretch", config={'displayModeBar': False})
            
    with col_asset:
        with st.container(border=True):
            st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase; margin-bottom: 10px;'>Asset Allocation</h5>", unsafe_allow_html=True)
            asset_df = get_asset_allocation(df_filtered)
            
            fig_asset = px.pie(
                asset_df,
                values="percentage",
                names="asset_class",
                hole=0.5,
                color_discrete_sequence=["#2E3192", "#F58220", "#10B981"],
                template="plotly_white"
            )
            fig_asset.update_traces(
                textinfo="percent",
                textposition="inside",
                hovertemplate="<b>Asset Class</b>: %{label}<br>Weight: %{value:.2f}%<extra></extra>"
            )
            fig_asset.update_layout(
                font_family="Inter, sans-serif",
                font_color="#0C1E36",
                height=360,
                margin=dict(l=10, r=10, t=10, b=90),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.12,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=9.5)
                )
            )
            st.plotly_chart(fig_asset, width="stretch", config={'displayModeBar': False})
            
    with col_mcap:
        with st.container(border=True):
            st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase; margin-bottom: 10px;'>Market Cap Allocation</h5>", unsafe_allow_html=True)
            mcap_df = get_market_cap_allocation(df_filtered)
            
            fig_mcap = px.bar(
                mcap_df,
                x="market_cap",
                y="percentage",
                labels={"market_cap": "Market Cap", "percentage": "Allocation Share (%)"},
                template="plotly_white"
            )
            fig_mcap.update_traces(
                marker_color="#F58220",
                opacity=0.9,
                hovertemplate="<b>Cap</b>: %{x}<br>Weight: %{y:.2f}%<extra></extra>"
            )
            fig_mcap.update_layout(
                font_family="Inter, sans-serif",
                font_color="#0C1E36",
                height=360,
                margin=dict(l=40, r=20, t=15, b=90),
                xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0")
            )
            st.plotly_chart(fig_mcap, width="stretch", config={'displayModeBar': False})
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600;'>Portfolio Holdings details</h4>", unsafe_allow_html=True)
    
    table_display = df_filtered[[
        "stock_name", "sector", "weight_pct", "market_cap", "scheme_name", "category"
    ]].rename(columns={
        "stock_name": "Holding Name",
        "sector": "Sector",
        "weight_pct": "Weight (%)",
        "market_cap": "Market Cap",
        "scheme_name": "Fund Name",
        "category": "Category"
    })
    
    table_display = table_display.sort_values("Weight (%)", ascending=False).reset_index(drop=True)
    st.dataframe(table_display, width="stretch", hide_index=True)


if __name__ == "__main__":
    render_layout("Portfolio Holdings", show)
