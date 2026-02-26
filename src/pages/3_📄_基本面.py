"""
基本面分析页面
估值分析、盈利能力、成长性、财务健康度、雷达图
"""


import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analysis.fundamental import FundamentalAnalyzer
from src.data.repository import Repository


def init_session_state():
    """初始化会话状态"""
    if "repository" not in st.session_state:
        st.session_state.repository = Repository("sqlite:///stock_analyzer.db")


def create_radar_chart(scores: dict) -> go.Figure:
    """创建雷达图

    Args:
        scores: 各维度评分字典

    Returns:
        go.Figure: Plotly雷达图对象
    """
    categories = list(scores.keys())
    values = list(scores.values())

    # 闭合图形
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure(
        data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='评分',
            line=dict(color='royalblue', width=2),
            fillcolor='rgba(65, 105, 225, 0.3)',
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
    )

    return fig


def create_score_gauge(score: int, title: str) -> go.Figure:
    """创建评分仪表盘

    Args:
        score: 评分值
        title: 标题

    Returns:
        go.Figure: Plotly仪表盘对象
    """
    # 根据分数确定颜色
    if score >= 80:
        color = "green"
    elif score >= 60:
        color = "yellowgreen"
    elif score >= 40:
        color = "orange"
    else:
        color = "red"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={'text': title, 'font': {'size': 14}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 60], 'color': "lightyellow"},
                    {'range': [60, 80], 'color': "lightgreen"},
                    {'range': [80, 100], 'color': "green"},
                ],
            },
        )
    )

    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig


def main():
    """主函数"""
    st.set_page_config(
        page_title="基本面分析 - 股票分析系统",
        page_icon="📄",
        layout="wide",
    )

    init_session_state()
    repo = st.session_state.repository
    analyzer = FundamentalAnalyzer(repo)

    st.title("📄 基本面分析")
    st.markdown("---")

    # 股票选择
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        watchlist = repo.get_watchlist()
        symbols = [item.symbol for item in watchlist]
        input_symbol = st.text_input("股票代码", placeholder="输入股票代码")
        selected_symbol = input_symbol.upper() if input_symbol else (symbols[0] if symbols else None)

    with col2:
        years = st.selectbox("分析年数", options=[3, 5, 7, 10], index=1)

    with col3:
        analyze_btn = st.button("开始分析", type="primary", use_container_width=True)

    if not selected_symbol:
        st.warning("请输入或选择股票代码")
        return

    st.markdown(f"**当前分析**: {selected_symbol}")

    # 执行基本面分析
    if analyze_btn or selected_symbol:
        with st.spinner("正在分析..."):
            report = analyzer.analyze(selected_symbol, years)

        if report.overall_score == 0:
            st.warning("无财务数据，无法进行基本面分析")
            return

        # 综合评分概览
        st.subheader("📊 综合评分")

        score_col1, score_col2, score_col3, score_col4, score_col5 = st.columns(5)

        with score_col1:
            fig = create_score_gauge(report.overall_score, "综合评分")
            st.plotly_chart(fig, use_container_width=True)

        with score_col2:
            if report.valuation:
                fig = create_score_gauge(report.valuation.score, "估值")
                st.plotly_chart(fig, use_container_width=True)

        with score_col3:
            if report.profitability:
                fig = create_score_gauge(report.profitability.score, "盈利能力")
                st.plotly_chart(fig, use_container_width=True)

        with score_col4:
            if report.growth:
                fig = create_score_gauge(report.growth.score, "成长性")
                st.plotly_chart(fig, use_container_width=True)

        with score_col5:
            if report.financial_health:
                fig = create_score_gauge(report.financial_health.score, "财务健康")
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # 雷达图
        st.subheader("🎯 综合评价雷达图")

        scores = {
            "估值": report.valuation.score if report.valuation else 50,
            "盈利能力": report.profitability.score if report.profitability else 50,
            "成长性": report.growth.score if report.growth else 50,
            "财务健康": report.financial_health.score if report.financial_health else 50,
        }

        radar_col1, radar_col2 = st.columns([2, 1])

        with radar_col1:
            fig = create_radar_chart(scores)
            st.plotly_chart(fig, use_container_width=True)

        with radar_col2:
            st.markdown("### 分析摘要")
            st.info(report.summary or "暂无摘要")

        st.markdown("---")

        # 估值分析
        st.subheader("💰 估值分析")
        if report.valuation:
            val_col1, val_col2, val_col3 = st.columns(3)

            with val_col1:
                st.metric("市盈率(PE)", f"{report.valuation.pe:.2f}" if report.valuation.pe else "--")

            with val_col2:
                st.metric("市净率(PB)", f"{report.valuation.pb:.2f}" if report.valuation.pb else "--")

            with val_col3:
                undervalued = "是" if report.valuation.is_undervalued else "否"
                st.metric("是否低估", undervalued if report.valuation.is_undervalued is not None else "--")

        st.markdown("---")

        # 盈利能力分析
        st.subheader("📈 盈利能力")
        if report.profitability:
            prof_col1, prof_col2, prof_col3, prof_col4 = st.columns(4)

            with prof_col1:
                st.metric("当前ROE", f"{report.profitability.roe_current:.2f}%" if report.profitability.roe_current else "--")

            with prof_col2:
                st.metric("3年平均ROE", f"{report.profitability.roe_avg_3y:.2f}%" if report.profitability.roe_avg_3y else "--")

            with prof_col3:
                st.metric("毛利率", f"{report.profitability.gross_margin:.2f}%" if report.profitability.gross_margin else "--")

            with prof_col4:
                st.metric("ROE趋势", report.profitability.roe_trend)

        st.markdown("---")

        # 成长性分析
        st.subheader("🚀 成长性")
        if report.growth:
            growth_col1, growth_col2, growth_col3 = st.columns(3)

            with growth_col1:
                st.metric("营收同比增长", f"{report.growth.revenue_yoy:.2f}%" if report.growth.revenue_yoy else "--")

            with growth_col2:
                st.metric("利润同比增长", f"{report.growth.profit_yoy:.2f}%" if report.growth.profit_yoy else "--")

            with growth_col3:
                st.metric("3年营收CAGR", f"{report.growth.revenue_cagr_3y:.2f}%" if report.growth.revenue_cagr_3y else "--")

        st.markdown("---")

        # 财务健康度
        st.subheader("🏥 财务健康度")
        if report.financial_health:
            health_col1, health_col2 = st.columns(2)

            with health_col1:
                st.metric("资产负债率", f"{report.financial_health.debt_ratio:.2f}%" if report.financial_health.debt_ratio else "--")

            with health_col2:
                st.metric("负债率趋势", report.financial_health.debt_trend or "--")

        st.markdown("---")

        # 财务数据表格
        st.subheader("📋 历史财务数据")
        financials = repo.get_financials(selected_symbol, years)

        if financials:
            df_data = {
                "报告期": [f.report_date for f in financials],
                "营业收入": [f"{f.revenue:.2f}亿" if f.revenue else "--" for f in financials],
                "净利润": [f"{f.net_profit:.2f}亿" if f.net_profit else "--" for f in financials],
                "ROE": [f"{f.roe:.2f}%" if f.roe else "--" for f in financials],
                "PE": [f"{f.pe:.2f}" if f.pe else "--" for f in financials],
                "PB": [f"{f.pb:.2f}" if f.pb else "--" for f in financials],
                "负债率": [f"{f.debt_ratio:.2f}%" if f.debt_ratio else "--" for f in financials],
                "毛利率": [f"{f.gross_margin:.2f}%" if f.gross_margin else "--" for f in financials],
            }
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无历史财务数据")


if __name__ == "__main__":
    main()
