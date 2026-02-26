"""
技术分析页面
K线图、技术指标、趋势分析、支撑压力位
"""


import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.analysis.indicators import calc_ma, calc_macd
from src.analysis.technical import TechnicalAnalyzer
from src.data.repository import Repository


def init_session_state():
    """初始化会话状态"""
    if "repository" not in st.session_state:
        st.session_state.repository = Repository("sqlite:///stock_analyzer.db")


def create_candlestick_chart(df: pd.DataFrame, indicators: dict = None) -> go.Figure:
    """创建K线图

    Args:
        df: 行情数据DataFrame
        indicators: 技术指标字典

    Returns:
        go.Figure: Plotly图表对象
    """
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=('K线图', '成交量', 'MACD')
    )

    # K线图
    fig.add_trace(
        go.Candlestick(
            x=df['trade_date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线',
        ),
        row=1, col=1
    )

    # 添加均线
    if indicators:
        if 'ma5' in indicators and indicators['ma5'] is not None:
            fig.add_trace(
                go.Scatter(x=df['trade_date'], y=df['ma5'], name='MA5', line=dict(color='orange', width=1)),
                row=1, col=1
            )
        if 'ma10' in indicators and indicators['ma10'] is not None:
            fig.add_trace(
                go.Scatter(x=df['trade_date'], y=df['ma10'], name='MA10', line=dict(color='blue', width=1)),
                row=1, col=1
            )
        if 'ma20' in indicators and indicators['ma20'] is not None:
            fig.add_trace(
                go.Scatter(x=df['trade_date'], y=df['ma20'], name='MA20', line=dict(color='purple', width=1)),
                row=1, col=1
            )

    # 成交量
    colors = ['red' if df['close'].iloc[i] >= df['open'].iloc[i] else 'green'
              for i in range(len(df))]
    fig.add_trace(
        go.Bar(x=df['trade_date'], y=df['volume'], name='成交量', marker_color=colors),
        row=2, col=1
    )

    # MACD
    if 'macd' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['trade_date'], y=df['macd'], name='MACD', line=dict(color='blue')),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['trade_date'], y=df['signal'], name='Signal', line=dict(color='orange')),
            row=3, col=1
        )

    fig.update_layout(
        height=800,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.update_xaxes(title_text="日期", row=3, col=1)
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)

    return fig


def main():
    """主函数"""
    st.set_page_config(
        page_title="技术分析 - 股票分析系统",
        page_icon="📈",
        layout="wide",
    )

    init_session_state()
    repo = st.session_state.repository
    analyzer = TechnicalAnalyzer(repo)

    st.title("📈 技术分析")
    st.markdown("---")

    # 股票选择
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # 获取自选股列表
        watchlist = repo.get_watchlist()
        symbols = [item.symbol for item in watchlist]

        # 允许手动输入
        input_symbol = st.text_input("股票代码", placeholder="输入股票代码")
        selected_symbol = input_symbol.upper() if input_symbol else (symbols[0] if symbols else None)

    with col2:
        days = st.selectbox("分析周期", options=[30, 60, 90, 180, 365], index=2)

    with col3:
        analyze_btn = st.button("开始分析", type="primary", use_container_width=True)

    if not selected_symbol:
        st.warning("请输入或选择股票代码")
        return

    st.markdown(f"**当前分析**: {selected_symbol}")

    # 执行技术分析
    if analyze_btn or selected_symbol:
        with st.spinner("正在分析..."):
            report = analyzer.analyze(selected_symbol, days)

        if report.score == 0:
            st.warning("数据不足，无法进行技术分析")
            return

        # 分析结果概览
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("技术评分", f"{report.score}", delta=None)

        with col2:
            if report.trend:
                st.metric("趋势方向", report.trend.direction)
            else:
                st.metric("趋势方向", "--")

        with col3:
            if report.trend:
                st.metric("当前价格", f"{report.trend.current_price:.2f}")
            else:
                st.metric("当前价格", "--")

        with col4:
            if report.support_resistance:
                st.metric("支撑位", f"{report.support_resistance.support_1:.2f}")
            else:
                st.metric("支撑位", "--")

        st.markdown("---")

        # K线图
        st.subheader("📊 K线图")

        # 获取行情数据
        quotes = repo.get_quotes(selected_symbol, days)
        if quotes:
            # 转换为DataFrame
            data = {
                "trade_date": [q.trade_date for q in quotes],
                "open": [float(q.open) for q in quotes],
                "high": [float(q.high) for q in quotes],
                "low": [float(q.low) for q in quotes],
                "close": [float(q.close) for q in quotes],
                "volume": [q.volume for q in quotes],
            }
            df = pd.DataFrame(data)
            df["trade_date"] = pd.to_datetime(df["trade_date"])
            df = df.sort_values("trade_date").reset_index(drop=True)

            # 计算指标
            ma_dict = calc_ma(df, [5, 10, 20])
            for period, values in ma_dict.items():
                df[f"ma{period}"] = values

            macd_result = calc_macd(df)
            if macd_result:
                # 添加MACD列（简化显示）
                pass

            # 创建K线图
            indicators = {
                "ma5": ma_dict.get(5),
                "ma10": ma_dict.get(10),
                "ma20": ma_dict.get(20),
            }
            fig = create_candlestick_chart(df, indicators)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # 技术指标详情
        st.subheader("📉 技术指标")
        ind_col1, ind_col2, ind_col3 = st.columns(3)

        if report.indicators:
            with ind_col1:
                st.markdown("### 均线系统")
                if report.indicators.ma5:
                    st.metric("MA5", f"{report.indicators.ma5:.2f}")
                if report.indicators.ma20:
                    st.metric("MA20", f"{report.indicators.ma20:.2f}")
                if report.indicators.ma60:
                    st.metric("MA60", f"{report.indicators.ma60:.2f}")

            with ind_col2:
                st.markdown("### MACD指标")
                if report.indicators.macd:
                    st.metric("DIF", f"{report.indicators.macd.dif:.4f}")
                    st.metric("DEA", f"{report.indicators.macd.dea:.4f}")
                    st.metric("MACD", f"{report.indicators.macd.macd:.4f}")
                    cross = "金叉" if report.indicators.macd.is_golden_cross() else "死叉"
                    st.metric("信号", cross)

            with ind_col3:
                st.markdown("### KDJ / RSI")
                if report.indicators.kdj:
                    st.metric("K", f"{report.indicators.kdj.k:.2f}")
                    st.metric("D", f"{report.indicators.kdj.d:.2f}")
                    st.metric("J", f"{report.indicators.kdj.j:.2f}")
                if report.indicators.rsi:
                    st.metric("RSI(14)", f"{report.indicators.rsi:.2f}")

        st.markdown("---")

        # 支撑压力位
        st.subheader("📍 支撑压力位")
        if report.support_resistance:
            sr_col1, sr_col2 = st.columns(2)

            with sr_col1:
                st.markdown("**压力位**")
                st.metric("第一压力位", f"{report.support_resistance.resistance_1:.2f}")
                if report.support_resistance.resistance_2:
                    st.metric("第二压力位", f"{report.support_resistance.resistance_2:.2f}")

            with sr_col2:
                st.markdown("**支撑位**")
                st.metric("第一支撑位", f"{report.support_resistance.support_1:.2f}")
                if report.support_resistance.support_2:
                    st.metric("第二支撑位", f"{report.support_resistance.support_2:.2f}")

        st.markdown("---")

        # K线形态
        st.subheader("🔮 K线形态")
        if report.patterns:
            for pattern in report.patterns:
                st.markdown(f"- {pattern}")
        else:
            st.info("未检测到明显的K线形态")


if __name__ == "__main__":
    main()
