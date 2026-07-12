"""Fund Recommender page."""
import sys
from pathlib import Path
import sqlite3
import textwrap
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from streamlit_app.components.layout import render_layout
from streamlit_app.services.recommender_service import (
    load_recommender_universe,
    get_recommendations,
    get_recommendation_insights
)

def clean_html(html_str: str) -> str:
    """Remove leading/trailing spaces from HTML lines."""
    return "\n".join([line.strip() for line in html_str.split("\n")])


def render_return_kpi_card(title: str, value: str, subtitle: str, color: str, icon: str) -> str:
    """Generate HTML for styled return metric card."""
    html_content = f"""
    <div class="fc-card" style="padding: 16px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 90px; height: 100%; margin-bottom: 0px; border-left: 4px solid {color}; font-family: 'Inter', sans-serif;">
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


def render_insight_kpi_card(title: str, fund_name: str, metric_value: str, color: str, icon: str) -> str:
    """Generate HTML for insight KPI card with long names."""
    html_content = f"""
    <div class="fc-card" style="padding: 16px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between; min-height: 120px; height: 100%; margin-bottom: 0px; border-left: 4px solid {color}; font-family: 'Inter', sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 4px; margin-bottom: 6px;">
            <span style="font-size: 10px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                {title}
            </span>
        </div>
        <div style="margin-top: 2px; margin-bottom: 4px; flex-grow: 1;">
            <div style="font-size: 13.5px; font-weight: 700; color: #0C1E36; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                {fund_name}
            </div>
        </div>
        <div style="font-size: 11px; color: {color}; font-weight: 600; margin-top: 4px;">
            {metric_value}
        </div>
    </div>
    """
    return clean_html(html_content)


def render_recommendation_card(rank: int, row: pd.Series, ret_col: str, horizon_lbl: str) -> str:
    """Generate HTML for a recommended fund card."""
    badges = {
        1: ("#1 RECOMMENDATION", "#FFD700", "#FFFDF0", "#B29600"),
        2: ("#2 RECOMMENDATION", "#C0C0C0", "#F9F9F9", "#6B6B6B"),
        3: ("#3 RECOMMENDATION", "#CD7F32", "#FFF9F5", "#93551A")
    }
    badge_text, border_color, bg_color, text_color = badges.get(rank, ("RECOMMENDATION", "#2E3192", "#F8FAFC", "#2E3192"))
    
    r1 = f"{row['return_1yr_pct']:.2f}%" if not pd.isna(row['return_1yr_pct']) else "N/A"
    r3 = f"{row['return_3yr_pct']:.2f}%" if not pd.isna(row['return_3yr_pct']) else "N/A"
    r5 = f"{row['return_5yr_pct']:.2f}%" if not pd.isna(row['return_5yr_pct']) else "N/A"
    sharpe = f"{row['sharpe_ratio']:.2f}" if not pd.isna(row['sharpe_ratio']) else "N/A"
    expense = f"{row['expense_ratio']:.2f}%" if not pd.isna(row['expense_ratio']) else "N/A"
    
    aum_val = row['aum']
    if not pd.isna(aum_val):
        aum_str = f"₹{aum_val / 100:.2f} Crore" if aum_val >= 100 else f"₹{aum_val / 100:.3f} Crore"
    else:
        aum_str = "N/A"

    html_content = f"""
    <div class="fc-card" style="padding: 24px; border-radius: 12px; border: 1px solid #E2E8F0; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between; height: 100%; min-height: 520px; font-family: 'Inter', sans-serif; transition: all 0.3s ease;">
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 11px; font-weight: 700; color: {text_color}; background-color: {bg_color}; border: 1px solid {border_color}; padding: 4px 10px; border-radius: 20px; letter-spacing: 0.5px; text-transform: uppercase;">
                    {badge_text}
                </span>
                <span style="font-size: 14px; font-weight: 800; color: #2E3192; background-color: rgba(46, 49, 146, 0.08); padding: 4px 10px; border-radius: 8px;">
                    {row['recommendation_score']}% Match
                </span>
            </div>
            
            <h4 style="color: #0C1E36; margin: 8px 0 4px 0; font-size: 17px; font-weight: 700; line-height: 1.3; min-height: 44px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                {row['scheme_name']}
            </h4>
            <div style="font-size: 12px; color: #64748B; margin-bottom: 12px; font-weight: 500;">
                {row['fund_house']}
            </div>
            
            <div style="display: flex; gap: 8px; margin-bottom: 18px; flex-wrap: wrap;">
                <span style="font-size: 10px; background-color: #F1F5F9; color: #475569; padding: 3px 8px; border-radius: 4px; font-weight: 600;">{row['category']}</span>
                <span style="font-size: 10px; background-color: #EFF6FF; color: #1D4ED8; padding: 3px 8px; border-radius: 4px; font-weight: 600;">{row['risk_category']} Risk</span>
                <span style="font-size: 10px; background-color: #FEF3C7; color: #D97706; padding: 3px 8px; border-radius: 4px; font-weight: 600;">{int(row['morningstar_rating'])} Stars</span>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; background: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; margin-bottom: 16px; text-align: center;">
                <div>
                    <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">1Y Ret (%)</div>
                    <div style="font-size: 13px; font-weight: 700; color: #10B981; margin-top: 3px;">{r1}</div>
                </div>
                <div>
                    <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">3Y Ret (%)</div>
                    <div style="font-size: 13px; font-weight: 700; color: #2E3192; margin-top: 3px;">{r3}</div>
                </div>
                <div>
                    <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">5Y Ret (%)</div>
                    <div style="font-size: 13px; font-weight: 700; color: #F58220; margin-top: 3px;">{r5}</div>
                </div>
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; font-size: 12.5px; color: #334155;">
                <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #E2E8F0; padding-bottom: 4px;">
                    <span style="color: #64748B; font-weight: 500;">Sharpe Ratio:</span>
                    <strong style="color: #0C1E36;">{sharpe}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #E2E8F0; padding-bottom: 4px;">
                    <span style="color: #64748B; font-weight: 500;">Expense Ratio (%):</span>
                    <strong style="color: #0C1E36;">{expense}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding-bottom: 4px;">
                    <span style="color: #64748B; font-weight: 500;">AUM (₹ Crore):</span>
                    <strong style="color: #0C1E36;">{aum_str}</strong>
                </div>
            </div>
        </div>
        
        <div style="background-color: #ECFDF5; border-left: 3px solid #10B981; border-radius: 6px; padding: 12px; font-size: 12px; color: #065F46; line-height: 1.4; font-weight: 500;">
            <div style="font-weight: 700; text-transform: uppercase; font-size: 9px; color: #047857; margin-bottom: 4px; letter-spacing: 0.5px;">Why recommended</div>
            {row['explanation']}
        </div>
    </div>
    """
    return clean_html(html_content)


def render_empty_state() -> None:
    """Render empty state when no funds match filters."""
    html_content = """
    <div class="coming-soon-container" style="padding: 50px 20px; border-style: dashed; border-width: 2px;">
        <span class="coming-soon-badge" style="background-color: rgba(220, 53, 69, 0.1); color: #dc3545;">No Recommendations Found</span>
        <h2 class="coming-soon-title" style="color: #dc3545; font-size: 20px;">No Funds Match the Selected Criteria</h2>
        <p class="coming-soon-subtitle" style="max-width: 500px; margin: 0 auto 20px auto;">
            Please adjust your inputs. The current combination of Goal, Risk Appetite, Horizon, and optional limits is too restrictive to yield qualifying funds.
        </p>
        <p style="color: #64748B; font-size: 13px;">Tip: Try increasing the Maximum Expense Ratio slider or selecting "All" categories or fund ratings.</p>
    </div>
    """
    st.markdown(
        clean_html(html_content),
        unsafe_allow_html=True
    )


def show() -> None:
    """Render the Fund Recommender content area."""
    try:
        raw_universe = load_recommender_universe()
    except Exception as e:
        st.error(f"Error loading mutual fund data from SQLite database: {e}")
        return

    fund_houses_list = ["All"] + sorted(raw_universe["fund_house"].dropna().unique().tolist())

    st.markdown(
        "<span style='color: #64748B; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;'>Investor Preferences & Inputs</span>",
        unsafe_allow_html=True
    )

    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    with col_i1:
        goal = st.selectbox(
            "Investment Goal:",
            options=["Wealth Creation", "Tax Saving", "Retirement", "Regular Income"],
            index=0,
            key="rec_goal",
            help="Goal for fund recommendation selection."
        )
    with col_i2:
        risk_appetite = st.selectbox(
            "Risk Appetite:",
            options=["Low", "Moderate", "High"],
            index=1,
            key="rec_risk",
            help="Risk tolerance constraint."
        )
    with col_i3:
        horizon = st.selectbox(
            "Investment Horizon:",
            options=["Less than 1 Year", "1–3 Years", "3–5 Years", "5+ Years"],
            index=2,
            key="rec_horizon",
            help="Matches recommendation holding periods."
        )
    with col_i4:
        category = st.selectbox(
            "Preferred Category:",
            options=["All", "Equity", "Debt"],
            index=0,
            key="rec_category",
            help="Asset class type constraint."
        )

    col_i5, col_i6, col_i7 = st.columns([1.5, 1, 1.5])
    with col_i5:
        fund_house = st.selectbox(
            "Preferred Fund House (optional):",
            options=fund_houses_list,
            index=0,
            key="rec_fund_house",
            help="AMC preference check."
        )
    with col_i6:
        min_rating = st.selectbox(
            "Minimum Rating (if available):",
            options=["All", "3 Stars", "4 Stars", "5 Stars"],
            index=0,
            key="rec_min_rating",
            help="Morningstar star filter."
        )
    with col_i7:
        max_expense = st.slider(
            "Maximum Expense Ratio:",
            min_value=0.5,
            max_value=2.0,
            value=2.0,
            step=0.05,
            format="%.2f%%",
            key="rec_max_expense",
            help="Expense ceiling filter."
        )

    rating_clean = "All"
    if min_rating != "All":
        rating_clean = min_rating.split(" ")[0]

    top3, match_universe = get_recommendations(
        goal=goal,
        risk_appetite=risk_appetite,
        horizon=horizon,
        category=category,
        fund_house=fund_house,
        min_rating=rating_clean,
        max_expense=max_expense
    )

    if top3.empty:
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
        render_empty_state()
        return

    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    horizon_mapping = {
        "Less than 1 Year": ("1Y Avg Return", "return_1yr_pct", "1-Year horizon proxy"),
        "1–3 Years": ("3Y Avg Return", "return_3yr_pct", "3-Year horizon proxy"),
        "3–5 Years": ("3Y Avg Return", "return_3yr_pct", "3-Year horizon proxy"),
        "5+ Years": ("5Y Avg Return", "return_5yr_pct", "5-Year horizon proxy")
    }
    ret_lbl, ret_col, ret_sub = horizon_mapping.get(horizon, ("3Y Avg Return", "return_3yr_pct", "3-Year horizon proxy"))

    avg_ret = match_universe[ret_col].mean()
    avg_sharpe = match_universe["sharpe_ratio"].mean()
    avg_expense = match_universe["expense_ratio"].mean()
    match_count = len(match_universe)

    with kpi_col1:
        st.markdown(
            render_return_kpi_card(
                ret_lbl,
                f"{avg_ret:.2f}%",
                ret_sub,
                "#2E3192",
                ""
            ),
            unsafe_allow_html=True
        )
    with kpi_col2:
        st.markdown(
            render_return_kpi_card(
                "Avg Sharpe Ratio",
                f"{avg_sharpe:.2f}",
                "Average risk-adjusted returns",
                "#3B82F6",
                ""
            ),
            unsafe_allow_html=True
        )
    with kpi_col3:
        st.markdown(
            render_return_kpi_card(
                "Avg Expense Ratio",
                f"{avg_expense:.2f}%",
                "Average fee costs",
                "#F58220",
                ""
            ),
            unsafe_allow_html=True
        )
    with kpi_col4:
        st.markdown(
            render_return_kpi_card(
                "Matches Found",
                f"{match_count} Funds",
                "Matching current inputs",
                "#10B981",
                ""
            ),
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
    st.markdown(
        clean_html("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;">
            <span style="font-size: 22px; line-height: 1;"></span>
            <span style="font-weight: 700; color: #2E3192; font-size: 16px; text-transform: uppercase; letter-spacing: 0.5px; font-family: 'Inter', sans-serif;">
                Top Recommended Mutual Funds
            </span>
        </div>
        """),
        unsafe_allow_html=True
    )

    card_col1, card_col2, card_col3 = st.columns(3)
    cols = [card_col1, card_col2, card_col3]

    for idx, (_, row) in enumerate(top3.iterrows()):
        with cols[idx]:
            st.markdown(
                render_recommendation_card(idx + 1, row, ret_col, ret_lbl),
                unsafe_allow_html=True
            )

    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

    st.markdown(
        clean_html("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 15px;">
            <span style="font-size: 20px; line-height: 1;"></span>
            <span style="font-weight: 700; color: #2E3192; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; font-family: 'Inter', sans-serif;">
                Recommendation Analytics
            </span>
        </div>
        """),
        unsafe_allow_html=True
    )

    vis_tabs = st.tabs([
        "Match Comparison",
        "Risk vs Return Profile",
        "Returns Breakdown",
        "Score Distribution"
    ])

    with vis_tabs[0]:
        fig_compare = px.bar(
            top3,
            x="recommendation_score",
            y="scheme_name",
            orientation="h",
            text="recommendation_score",
            color="scheme_name",
            color_discrete_sequence=["#2E3192", "#3B82F6", "#F58220"],
            labels={
                "recommendation_score": "Recommendation Score (% Match)",
                "scheme_name": "Scheme Name"
            },
            template="plotly_white"
        )
        fig_compare.update_traces(
            textposition="inside",
            texttemplate="%{text}% Match",
            hovertemplate="<b>%{y}</b><br>Match Score: %{x}%<extra></extra>"
        )
        fig_compare.update_layout(
            showlegend=False,
            height=380,
            margin=dict(l=40, r=20, t=10, b=40),
            xaxis=dict(range=[0, 105], showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(showgrid=False),
            font_family="Inter, sans-serif"
        )
        st.plotly_chart(fig_compare, width="stretch", config={'displayModeBar': False})

    with vis_tabs[1]:
        scatter_df = match_universe.dropna(subset=["std_dev", "return_3yr_pct"]).copy()
        scatter_df["is_recommended"] = scatter_df["amfi_code"].isin(top3["amfi_code"])
        scatter_df["highlight_label"] = scatter_df["is_recommended"].map({True: "Recommended", False: "Universe Match"})
        
        fig_scatter = px.scatter(
            scatter_df,
            x="std_dev",
            y="return_3yr_pct",
            size="aum",
            color="highlight_label",
            color_discrete_map={"Recommended": "#EF4444", "Universe Match": "#3B82F6"},
            hover_name="scheme_name",
            hover_data={
                "category": True,
                "std_dev": ":.2f%",
                "return_3yr_pct": ":.2f%",
                "aum": ":,.2f Cr",
                "sharpe_ratio": ":.2f",
                "highlight_label": False
            },
            labels={
                "std_dev": "Volatility (Std Deviation %)",
                "return_3yr_pct": "3-Year Annual Return (%)",
                "aum": "AUM (₹ Crore)",
                "color": "Fund Status"
            },
            template="plotly_white"
        )
        fig_scatter.update_traces(
            marker=dict(line=dict(width=1, color='DarkSlateGrey')),
            selector=dict(mode='markers')
        )
        fig_scatter.update_layout(
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
            height=380,
            margin=dict(l=40, r=20, t=10, b=40),
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            font_family="Inter, sans-serif"
        )
        st.plotly_chart(fig_scatter, width="stretch", config={'displayModeBar': False})

    with vis_tabs[2]:
        fig_returns = go.Figure()
        fig_returns.add_trace(go.Bar(
            name="1Y Return",
            x=top3["scheme_name"],
            y=top3["return_1yr_pct"],
            marker_color="#3B82F6",
            hovertemplate="<b>%{x}</b><br>1Y Return: %{y:.2f}%<extra></extra>"
        ))
        fig_returns.add_trace(go.Bar(
            name="3Y Return",
            x=top3["scheme_name"],
            y=top3["return_3yr_pct"],
            marker_color="#2E3192",
            hovertemplate="<b>%{x}</b><br>3Y Return: %{y:.2f}%<extra></extra>"
        ))
        fig_returns.add_trace(go.Bar(
            name="5Y Return",
            x=top3["scheme_name"],
            y=top3["return_5yr_pct"],
            marker_color="#F58220",
            hovertemplate="<b>%{x}</b><br>5Y Return: %{y:.2f}%<extra></extra>"
        ))
        
        fig_returns.update_layout(
            barmode="group",
            template="plotly_white",
            height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=20, t=10, b=40),
            xaxis=dict(showgrid=False),
            yaxis=dict(title="Annualized Return (%)", showgrid=True, gridcolor="#F1F5F9"),
            font_family="Inter, sans-serif"
        )
        st.plotly_chart(fig_returns, width="stretch", config={'displayModeBar': False})

    with vis_tabs[3]:
        fig_dist = px.histogram(
            match_universe,
            x="recommendation_score",
            nbins=20,
            color_discrete_sequence=["#94A3B8"],
            labels={"recommendation_score": "Match Score (%)", "count": "Fund Count"},
            template="plotly_white"
        )
        
        counts, _ = np.histogram(match_universe["recommendation_score"].dropna(), bins=20)
        max_y = int(counts.max()) if len(counts) > 0 else 5
        
        colors_list = ["#B29600", "#6B6B6B", "#93551A"]
        bg_colors = ["#FFFDF0", "#F9F9F9", "#FFF9F5"]
        emojis = ["", "", ""]
        y_positions = [max_y * 0.85, max_y * 0.60, max_y * 0.35]
        
        for i, score_val in enumerate(top3["recommendation_score"]):
            color = colors_list[i % len(colors_list)]
            bg_color = bg_colors[i % len(bg_colors)]
            emoji = emojis[i % len(emojis)]
            y_pos = y_positions[i % len(y_positions)]
            
            fig_dist.add_vline(
                x=score_val,
                line_dash="dash",
                line_width=1.5,
                line_color=color
            )
            
            fig_dist.add_annotation(
                x=score_val,
                y=y_pos,
                text=f"{emoji} #{i+1} ({score_val}%)",
                showarrow=True,
                arrowhead=2,
                arrowcolor=color,
                arrowsize=1.2,
                arrowwidth=1.5,
                ax=-45 if i % 2 == 0 else 45,
                ay=-25,
                bgcolor=bg_color,
                bordercolor=color,
                borderwidth=1,
                borderpad=4,
                font=dict(size=10, family="Inter, sans-serif", color="#0C1E36")
            )

        fig_dist.update_layout(
            height=380,
            margin=dict(l=40, r=20, t=50, b=40),
            xaxis=dict(title="Recommendation Score (% Match)", showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(title="Number of Funds", showgrid=True, gridcolor="#F1F5F9", range=[0, max_y * 1.15]),
            font_family="Inter, sans-serif"
        )
        st.plotly_chart(fig_dist, width="stretch", config={'displayModeBar': False})

    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
    st.markdown(
        clean_html("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 15px;">
            <span style="font-size: 20px; line-height: 1;"></span>
            <span style="font-weight: 700; color: #2E3192; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; font-family: 'Inter', sans-serif;">
                Recommendation Insights
            </span>
        </div>
        """),
        unsafe_allow_html=True
    )

    insights = get_recommendation_insights(top3, match_universe)

    ins_col1, ins_col2, ins_col3 = st.columns(3)
    with ins_col1:
        st.markdown(
            render_insight_kpi_card(
                "Best Overall Match",
                insights["best_overall_name"],
                insights["best_overall_val"],
                "#2E3192",
                ""
            ),
            unsafe_allow_html=True
        )
    with ins_col2:
        st.markdown(
            render_insight_kpi_card(
                "Best Low-Risk Match",
                insights["best_low_risk_name"],
                insights["best_low_risk_val"],
                "#10B981",
                ""
            ),
            unsafe_allow_html=True
        )
    with ins_col3:
        st.markdown(
            render_insight_kpi_card(
                "Best Value (Efficiency)",
                insights["best_value_name"],
                insights["best_value_val"],
                "#8B5CF6",
                ""
            ),
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
    st.markdown(
        clean_html("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 15px;">
            <span style="font-size: 20px; line-height: 1;"></span>
            <span style="font-weight: 700; color: #2E3192; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; font-family: 'Inter', sans-serif;">
                Top Recommendations Table
            </span>
        </div>
        """),
        unsafe_allow_html=True
    )

    matrix_df = match_universe[[
        "recommendation_score",
        "scheme_name",
        "fund_house",
        "category",
        "risk_category",
        "morningstar_rating",
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "sharpe_ratio",
        "expense_ratio",
        "aum"
    ]].copy()

    matrix_df.columns = [
        "Score (% Match)",
        "Scheme Name",
        "Fund House",
        "Category",
        "Risk Level",
        "Rating (Stars)",
        "1Y Return (%)",
        "3Y Return (%)",
        "5Y Return (%)",
        "Sharpe Ratio",
        "Expense Ratio (%)",
        "AUM (₹ Crore)"
    ]

    matrix_df = matrix_df.sort_values(by="Score (% Match)", ascending=False).reset_index(drop=True)

    ALL_LABEL = "All Recommended Funds"
    fund_options = [ALL_LABEL] + [
        f"{row['Scheme Name']}  ·  {row['Fund House']}"
        for _, row in matrix_df.iterrows()
    ]

    st.markdown(
        """
        <div style="
            font-size: 12px;
            font-weight: 600;
            color: #475569;
            font-family: 'Inter', sans-serif;
            letter-spacing: 0.3px;
            margin-bottom: 4px;
        ">
            Search or select a recommended mutual fund
        </div>
        """,
        unsafe_allow_html=True
    )

    selected_option = st.selectbox(
        label="fund_selector_label",
        options=fund_options,
        index=0,
        placeholder="Search or select a recommended mutual fund...",
        label_visibility="collapsed",
        key="fund_table_selector"
    )

    if selected_option != ALL_LABEL:
        selected_scheme = selected_option.split("  ·  ")[0].strip()
        matrix_df = matrix_df[matrix_df["Scheme Name"] == selected_scheme]

    formatted_matrix = matrix_df.style.format({
        "Score (% Match)": "{:.2f}%",
        "1Y Return (%)": "{:.2f}%",
        "3Y Return (%)": "{:.2f}%",
        "5Y Return (%)": "{:.2f}%",
        "Sharpe Ratio": "{:.2f}",
        "Expense Ratio (%)": "{:.2f}%",
        "AUM (₹ Crore)": "{:,.2f}"
    })

    st.dataframe(
        formatted_matrix,
        width="stretch",
        hide_index=True
    )


if __name__ == "__main__":
    render_layout("Fund Recommender", show)
