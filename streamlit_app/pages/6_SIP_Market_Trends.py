"""SIP & Market Trends page."""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from streamlit_app.components.layout import render_layout
from streamlit_app.helpers import clean_html
from streamlit_app.services.sip_service import (
    load_sip_market_data,
    load_category_inflows_data,
    get_filter_options,
    filter_sip_data,
    filter_cat_data,
    calculate_sip_kpis,
    get_top_categories_fy25,
    generate_category_summary_table,
    generate_sip_insights,
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
    """Render the SIP & Market Trends dashboard."""
    st.markdown(
        """
        <h2 style="color:#0C1E36;margin-bottom:5px;">
            SIP & Market Trends
        </h2>
        <p style="color:#64748B;font-size:16px;">
            Analyze industry-wide SIP inflows, category asset flows, and benchmark index market trends
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    raw_sip_df = load_sip_market_data()
    raw_cat_df = load_category_inflows_data()
    filter_opts = get_filter_options(raw_sip_df, raw_cat_df)
    
    st.markdown(
        "<span style='color: #64748B; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;'>SIP filter control deck</span>", 
        unsafe_allow_html=True
    )
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        selected_years = st.multiselect(
            "Year:",
            options=filter_opts["years"],
            placeholder="All Years",
            key="sip_year_filter"
        )
    with col_f2:
        selected_quarters = st.multiselect(
            "Quarter:",
            options=filter_opts["quarters"],
            placeholder="All Quarters",
            key="sip_quarter_filter"
        )
    with col_f3:
        selected_categories = st.multiselect(
            "Category:",
            options=filter_opts["categories"],
            placeholder="All Categories",
            key="sip_cat_filter"
        )
        
    df_sip_filtered = filter_sip_data(
        raw_sip_df,
        years=selected_years,
        quarters=selected_quarters
    )
    
    df_cat_filtered = filter_cat_data(
        raw_cat_df,
        years=selected_years,
        categories=selected_categories,
        quarters=selected_quarters
    )
    
    if df_sip_filtered.empty:
        st.warning("⚠️ No SIP trend data matches the selected filter criteria. Please adjust your filters.")
        return
        
    kpis = calculate_sip_kpis(df_sip_filtered)
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1:
        st.markdown(
            render_return_kpi_card(
                "Latest Monthly SIP Inflow (₹ Crore)",
                f"₹{kpis['latest_inflow']:,.2f} Crore",
                "For the month of " + str(df_sip_filtered.iloc[-1]['month_str']),
                "#2E3192",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol2:
        st.markdown(
            render_return_kpi_card(
                "Total SIP Inflow (₹ Crore)",
                f"₹{kpis['total_inflow']:,.2f} Crore",
                "Cumulative period inflow volume",
                "#F58220",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol3:
        st.markdown(
            render_return_kpi_card(
                "Highest Monthly SIP Inflow (₹ Crore)",
                f"₹{kpis['highest_inflow_val']:,.2f} Crore",
                f"Achieved in {kpis['highest_inflow_month']}",
                "#10B981",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol4:
        st.markdown(
            render_return_kpi_card(
                "YoY Growth (%)",
                f"{kpis['yoy_growth']:.2f}%",
                "Latest month-on-month yearly trend",
                "#3B82F6",
                ""
            ),
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    col_dual, col_top5 = st.columns([58, 42])
    
    with col_dual:
        with st.container(border=True):
            fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_dual.add_trace(
                go.Bar(
                    x=df_sip_filtered["month_str"],
                    y=df_sip_filtered["sip_inflow_crore"],
                    name="SIP Inflow (₹ Crore)",
                    marker_color="#2E3192",
                    opacity=0.9,
                    hovertemplate="<b>Month</b>: %{x}<br>SIP Inflow: ₹%{y:,.2f} Crore<extra></extra>"
                ),
                secondary_y=False
            )
            
            if "nifty_close" in df_sip_filtered.columns and not df_sip_filtered["nifty_close"].isna().all():
                fig_dual.add_trace(
                    go.Scatter(
                        x=df_sip_filtered["month_str"],
                        y=df_sip_filtered["nifty_close"],
                        name="NIFTY 50 Index",
                        line=dict(color="#F58220", width=3),
                        hovertemplate="<b>Month</b>: %{x}<br>NIFTY 50: %{y:,.2f}<extra></extra>"
                    ),
                    secondary_y=True
                )
                
            fig_dual.update_layout(
                title=dict(
                    text="Monthly SIP Inflow vs NIFTY 50 Index Trend",
                    font=dict(size=14, color="#0C1E36", family="Inter, sans-serif"),
                    x=0.02,
                    xanchor="left",
                    y=0.95
                ),
                template="plotly_white",
                font_family="Inter, sans-serif",
                font_color="#0C1E36",
                height=460,
                margin=dict(l=55, r=45, t=75, b=85),
                xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
                yaxis=dict(
                    title=dict(text="SIP Inflow (₹ Crore)", standoff=15),
                    showgrid=True,
                    gridcolor="#F1F5F9",
                    linecolor="#E2E8F0"
                ),
                yaxis2=dict(
                    title=dict(text="NIFTY 50 Close", standoff=20),
                    showgrid=False,
                    linecolor="#E2E8F0"
                ),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.18,
                    xanchor="center",
                    x=0.5
                )
            )
            st.plotly_chart(fig_dual, width="stretch", config={'displayModeBar': False})
            
    with col_top5:
        with st.container(border=True):
            top_cat_df = get_top_categories_fy25(df_cat_filtered)
            
            fig_top_cat = px.bar(
                top_cat_df,
                x="total_inflow",
                y="category",
                orientation="h",
                labels={"total_inflow": "Total Net Inflow (₹ Crore)", "category": "Category"},
                template="plotly_white"
            )
            fig_top_cat.update_traces(
                marker_color="#2E3192",
                opacity=0.9,
                hovertemplate="<b>Category</b>: %{y}<br>Inflow: ₹%{x:,.2f} Crore<extra></extra>"
            )
            fig_top_cat.update_yaxes(categoryorder="total ascending")
            
            fig_top_cat.update_layout(
                title=dict(
                    text="Top 5 Categories by Net Inflow (FY25)",
                    font=dict(size=14, color="#0C1E36", family="Inter, sans-serif"),
                    x=0.02,
                    xanchor="left",
                    y=0.95
                ),
                font_family="Inter, sans-serif",
                font_color="#0C1E36",
                height=460,
                margin=dict(l=120, r=30, t=75, b=85),
                xaxis=dict(
                    title=dict(text="Total Net Inflow (₹ Crore)", standoff=15),
                    showgrid=True,
                    gridcolor="#F1F5F9",
                    linecolor="#E2E8F0"
                ),
                yaxis=dict(
                    title=None,
                    showgrid=False,
                    linecolor="#E2E8F0"
                )
            )
            st.plotly_chart(fig_top_cat, width="stretch", config={'displayModeBar': False})
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    col_heatmap, col_insights = st.columns([2, 1])
    
    with col_heatmap:
        if not df_cat_filtered.empty:
            with st.container(border=True):
                pivot_df = df_cat_filtered.pivot(index="category", columns="month_str", values="net_inflow_crore").fillna(0)
                
                fig_heatmap = go.Figure(
                    data=go.Heatmap(
                        z=pivot_df.values,
                        x=pivot_df.columns,
                        y=pivot_df.index,
                        colorscale="Blues",
                        text=pivot_df.values,
                        texttemplate="%{text:.0f}",
                        hovertemplate="<b>Category</b>: %{y}<br><b>Month</b>: %{x}<br>Net Inflow: ₹%{z:,.2f} Crore<extra></extra>"
                    )
                )
                fig_heatmap.update_layout(
                    title=dict(
                        text="Category Net Inflow Heatmap (₹ Crore)", 
                        font=dict(size=14, color="#0C1E36", family="Inter, sans-serif"),
                        x=0.5,
                        xanchor="center",
                        y=0.95
                    ),
                    font_family="Inter, sans-serif",
                    font_color="#0C1E36",
                    height=420,
                    margin=dict(l=100, r=20, t=80, b=40),
                    xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
                    yaxis=dict(showgrid=False, linecolor="#E2E8F0")
                )
                st.plotly_chart(fig_heatmap, width="stretch", config={'displayModeBar': False})
        else:
            st.warning("⚠️ No category net inflows records available for the selected filters.")
            
    with col_insights:
        insights = generate_sip_insights(df_sip_filtered, df_cat_filtered)
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="min-height: 420px; display: flex; flex-direction: column; justify-content: space-between; font-family: 'Inter', sans-serif;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                            <span style="font-size: 20px; line-height: 1;"></span>
                            <span style="font-weight: 700; color: #2E3192; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Market Insights</span>
                        </div>
                        <ul style="font-size: 12.5px; color: #475569; line-height: 1.5; padding-left: 20px; margin: 0;">
                            <li style="margin-bottom: 8px;">
                                <strong>Highest Inflow Month:</strong><br>
                                <strong>{insights['highest_sip_month']}</strong> peaked at <strong>₹{insights['highest_sip_val']:,.2f} Crore</strong>.
                            </li>
                            <li style="margin-bottom: 8px;">
                                <strong>Lowest Inflow Month:</strong><br>
                                <strong>{insights['lowest_sip_month']}</strong> registered <strong>₹{insights['lowest_sip_val']:,.2f} Crore</strong>.
                            </li>
                            <li style="margin-bottom: 8px;">
                                <strong>Highest Inflow YoY Growth:</strong><br>
                                <strong>{insights['highest_growth_month']}</strong> grew by <strong>{insights['highest_growth_val']:.2f}%</strong> YoY.
                            </li>
                            <li style="margin-bottom: 8px;">
                                <strong>Best Performing Category:</strong><br>
                                <strong>{insights['best_performing_category']}</strong> leads with a total of <strong>₹{insights['best_category_val']:,.2f} Crore</strong> net inflows.
                            </li>
                            <li style="margin-bottom: 0px;">
                                <strong>Market Correlation (NIFTY vs SIP):</strong><br>
                                Correlation coefficient: <strong>{insights['correlation_coef']:.2f}</strong>. This suggests a <strong>{insights['market_relationship']}</strong>.
                            </li>
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600;'>Category Inflows summary</h4>", unsafe_allow_html=True)
    
    summary_table = generate_category_summary_table(df_cat_filtered)
    
    summary_display = summary_table.copy()
    summary_display["Net Inflow"] = summary_display["Net Inflow"].map(lambda x: f"₹{x:,.2f}")
    summary_display["Avg Monthly Inflow"] = summary_display["Avg Monthly Inflow"].map(lambda x: f"₹{x:,.2f}")
    summary_display["YoY Growth"] = summary_display["YoY Growth"].map(lambda x: f"{x:.2f}%")
    summary_display["Market Share"] = summary_display["Market Share"].map(lambda x: f"{x:.2f}%")
    
    summary_display = summary_display.rename(columns={
        "category": "Category",
        "Net Inflow": "Net Inflow (₹ Crore)",
        "Avg Monthly Inflow": "Avg Monthly Inflow (₹ Crore)",
        "YoY Growth": "YoY Growth (%)",
        "Market Share": "Market Share (%)"
    })
    
    st.dataframe(summary_display, width="stretch", hide_index=True)


if __name__ == "__main__":
    render_layout("SIP & Market Trends", show)
