"""Investor Analytics page."""
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
from streamlit_app.services.investor_service import (
    load_investor_data,
    get_filter_options,
    filter_investor_data,
    calculate_investor_kpis,
    aggregate_transaction_by_state,
    aggregate_investment_type_distribution,
    aggregate_age_group_analysis,
    aggregate_monthly_trend,
    generate_investor_insights,
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
    """Render the Investor Analytics dashboard."""
    st.markdown(
        """
        <h2 style="color:#0C1E36;margin-bottom:5px;">
            Investor Analytics
        </h2>
        <p style="color:#64748B;font-size:16px;">
            Analyze investor demographics, transaction patterns, and investment preferences across regions
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    raw_df = load_investor_data()
    filter_opts = get_filter_options(raw_df)
    
    st.markdown(
        "<span style='color: #64748B; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;'>Demographic filters deck</span>", 
        unsafe_allow_html=True
    )
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        selected_states = st.multiselect(
            "State:",
            options=filter_opts["states"],
            placeholder="All States",
            key="inv_state_filter"
        )
    with col_f2:
        selected_ages = st.multiselect(
            "Age Group:",
            options=filter_opts["age_groups"],
            placeholder="All Age Brackets",
            key="inv_age_filter"
        )
    with col_f3:
        selected_tiers = st.multiselect(
            "City Tier:",
            options=filter_opts["city_tiers"],
            placeholder="All City Tiers",
            key="inv_tier_filter"
        )
        
    df_filtered = filter_investor_data(
        raw_df,
        states=selected_states,
        age_groups=selected_ages,
        city_tiers=selected_tiers
    )
    
    if df_filtered.empty:
        st.warning("⚠️ No transactions match the selected filter criteria. Please adjust your filters.")
        return
        
    kpis = calculate_investor_kpis(df_filtered)
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1:
        st.markdown(
            render_return_kpi_card(
                "Total Investors (Count)",
                f"{kpis['total_investors']:,}",
                "Unique investing entities",
                "#2E3192",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol2:
        st.markdown(
            render_return_kpi_card(
                "Total Transactions (Count)",
                f"{kpis['total_transactions']:,}",
                "Aggregate transaction volume",
                "#F58220",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol3:
        st.markdown(
            render_return_kpi_card(
                "Average SIP (₹)",
                f"₹{kpis['avg_sip_amount']:,.2f}",
                "Mean monthly SIP installment",
                "#10B981",
                ""
            ),
            unsafe_allow_html=True
        )
    with kcol4:
        st.markdown(
            render_return_kpi_card(
                "Avg Transaction (₹)",
                f"₹{kpis['avg_transaction_amount']:,.2f}",
                "Mean absolute transaction size",
                "#3B82F6",
                ""
            ),
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    
    col_state, col_donut = st.columns([2, 1])
    
    with col_state:
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Transaction Volume by State (₹ Crore)</h5>", unsafe_allow_html=True)
        state_df = aggregate_transaction_by_state(df_filtered)
        
        fig_state = px.bar(
            state_df,
            x="state",
            y="total_amount_cr",
            labels={"state": "State", "total_amount_cr": "Total Amount (₹ Crore)"},
            template="plotly_white"
        )
        fig_state.update_traces(
            marker_color="#2E3192",
            opacity=0.9,
            hovertemplate="<b>State</b>: %{x}<br>Invested: ₹%{y:.2f} Crore<extra></extra>"
        )
        fig_state.update_layout(
            font_family="Inter, sans-serif",
            font_color="#0C1E36",
            height=350,
            margin=dict(l=40, r=20, t=10, b=40),
            xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0")
        )
        st.plotly_chart(fig_state, width="stretch", config={'displayModeBar': False})
        
    with col_donut:
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Investment Type Distribution</h5>", unsafe_allow_html=True)
        type_df = aggregate_investment_type_distribution(df_filtered)
        
        fig_donut = px.pie(
            type_df,
            values="total_amount_cr",
            names="transaction_type",
            hole=0.5,
            color_discrete_sequence=["#2E3192", "#F58220", "#10B981"],
            template="plotly_white"
        )
        fig_donut.update_traces(
            textinfo="percent",
            textposition="inside",
            hovertemplate="<b>Type</b>: %{label}<br>Amount: ₹%{value:.2f} Crore<br>Share: %{percent}<extra></extra>"
        )
        fig_donut.update_layout(
            font_family="Inter, sans-serif",
            font_color="#0C1E36",
            height=350,
            margin=dict(l=20, r=20, t=10, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_donut, width="stretch", config={'displayModeBar': False})
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    col_trend, col_insights = st.columns([2, 1])
    
    with col_trend:
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Monthly Transaction Volume Trend (Count)</h5>", unsafe_allow_html=True)
        monthly_df = aggregate_monthly_trend(df_filtered)
        
        fig_trend = px.line(
            monthly_df,
            x="month_str",
            y="transaction_count",
            labels={"month_str": "Month", "transaction_count": "Transactions"},
            template="plotly_white"
        )
        fig_trend.update_traces(
            line_color="#2E3192",
            line_width=3,
            hovertemplate="<b>Month</b>: %{x}<br>Transactions: %{y:,}<extra></extra>"
        )
        fig_trend.update_layout(
            font_family="Inter, sans-serif",
            font_color="#0C1E36",
            height=350,
            margin=dict(l=40, r=20, t=10, b=40),
            xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0")
        )
        st.plotly_chart(fig_trend, width="stretch", config={'displayModeBar': False})
        
    with col_insights:
        insights = generate_investor_insights(df_filtered)
        
        st.markdown(
            f"""
            <div class="fc-card" style="padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%; margin-bottom: 0px; min-height: 350px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-family: 'Inter', sans-serif;">
                        <span style="font-size: 20px; line-height: 1;"></span>
                        <span style="font-weight: 700; color: #2E3192; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Investor Insights</span>
                    </div>
                    <ul style="font-size: 12.5px; color: #475569; line-height: 1.5; padding-left: 20px; margin: 0; font-family: 'Inter', sans-serif;">
                        <li style="margin-bottom: 8px;">
                            <strong>Highest Investing State:</strong><br>
                            <span style="color: #2E3192; font-weight: 600;">{insights['highest_investing_state']}</span> (₹{insights['highest_state_amount_cr']:.2f} Cr)
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Most Active Age Bracket:</strong><br>
                            Age group <strong>{insights['most_active_age_group']}</strong> leads with <strong>{insights['most_active_age_count']:,}</strong> transactions.
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Preferred Asset Type:</strong><br>
                            <strong>{insights['preferred_investment_type']}</strong> captures <strong>{insights['preferred_type_pct']:.1f}%</strong> of total funding volume.
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Highest Average SIP:</strong><br>
                            Age group <strong>{insights['highest_avg_sip_age_group']}</strong> averages <strong>₹{insights['highest_avg_sip_val']:,.2f}</strong> per monthly SIP.
                        </li>
                        <li style="margin-bottom: 8px;">
                            <strong>Top Contributing City Tier:</strong><br>
                            <strong>{insights['top_contributing_city_tier']}</strong> contributes <strong>{insights['top_city_tier_pct']:.1f}%</strong> of demographic deposits.
                        </li>
                        <li style="margin-bottom: 0px;">
                            <strong>Monthly Growth Trend:</strong><br>
                            Last month transaction capital shifted by <strong>{insights['monthly_growth_rate']:.2f}%</strong>.
                        </li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    col_age, col_leaders = st.columns(2)
    
    with col_age:
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Age Group vs Average SIP Amount (₹)</h5>", unsafe_allow_html=True)
        age_sip_df = aggregate_age_group_analysis(df_filtered)
        
        fig_age = px.bar(
            age_sip_df,
            x="age_group",
            y="avg_sip",
            labels={"age_group": "Age Group", "avg_sip": "Average SIP Amount (₹)"},
            template="plotly_white"
        )
        fig_age.update_traces(
            marker_color="#F58220",
            opacity=0.9,
            hovertemplate="<b>Age Group</b>: %{x}<br>Avg SIP: ₹%{y:,.2f}<extra></extra>"
        )
        fig_age.update_layout(
            font_family="Inter, sans-serif",
            font_color="#0C1E36",
            height=350,
            margin=dict(l=40, r=20, t=10, b=40),
            xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0")
        )
        st.plotly_chart(fig_age, width="stretch", config={'displayModeBar': False})
        
    with col_leaders:
        st.markdown("<h5 style='color: #475569; font-weight: 600; font-size: 13px; text-transform: uppercase;'>Top Geographic Contributions</h5>", unsafe_allow_html=True)
        state_leaders = state_df.head(5).rename(columns={"state": "State", "total_amount_cr": "Total Invested (₹ Crore)"})
        city_leaders = df_filtered.groupby("city")["amount_inr"].sum().reset_index()
        city_leaders["total_amount_cr"] = city_leaders["amount_inr"] / 10000000.0
        city_leaders = city_leaders.sort_values("total_amount_cr", ascending=False).head(5)[["city", "total_amount_cr"]].rename(columns={"city": "City", "total_amount_cr": "Total Invested (₹ Crore)"})
        
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.markdown("<span style='font-size: 11px; font-weight:600; color:#2E3192;'>Top 5 States</span>", unsafe_allow_html=True)
            st.dataframe(state_leaders, width="stretch", hide_index=True)
        with t_col2:
            st.markdown("<span style='font-size: 11px; font-weight:600; color:#F58220;'>Top 5 Cities</span>", unsafe_allow_html=True)
            st.dataframe(city_leaders, width="stretch", hide_index=True)
            
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #0C1E36; font-family: Inter, sans-serif; font-weight: 600;'>Investor Details Dashboard</h4>", unsafe_allow_html=True)
    
    table_display = df_filtered[[
        "state", "city_tier", "age_group", "transaction_type", "amount_inr", "full_date"
    ]].copy()
    
    table_display["full_date"] = table_display["full_date"].dt.strftime("%d %b %Y")
    table_display = table_display.rename(columns={
        "state": "Investor State",
        "city_tier": "City Tier",
        "age_group": "Age Group",
        "transaction_type": "Investment Type",
        "amount_inr": "Transaction Amount (₹)",
        "full_date": "Transaction Date"
    })
    table_display = table_display.sort_values("Transaction Date", ascending=False)
    
    st.dataframe(table_display, width="stretch", hide_index=True)


if __name__ == "__main__":
    render_layout("Investor Analytics", show)
