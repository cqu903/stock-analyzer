"""
量化选股页面
根据预设策略筛选符合条件的股票
"""

from datetime import datetime

import streamlit as st

from src.data.repository import Repository
from src.models.schemas import Market
from src.screening.screener import StockScreener
from src.screening.strategies import StrategyRegistry


def init_session_state():
    """初始化会话状态"""
    if "repository" not in st.session_state:
        st.session_state.repository = Repository("sqlite:///stock_analyzer.db")
    if "screen_results" not in st.session_state:
        st.session_state.screen_results = []
    if "selected_symbols" not in st.session_state:
        st.session_state.selected_symbols = set()


def render_stars(score: float) -> str:
    """根据评分生成星级显示"""
    if score >= 90:
        return "⭐⭐⭐⭐⭐"
    elif score >= 75:
        return "⭐⭐⭐⭐"
    elif score >= 60:
        return "⭐⭐⭐"
    elif score >= 40:
        return "⭐⭐"
    else:
        return "⭐"


def render_match_details(details: dict) -> str:
    """格式化显示匹配详情"""
    parts = []
    for key, value in details.items():
        if isinstance(value, float):
            if "growth" in key or "yoy" in key:
                parts.append(f"{key}: {value:.1f}%")
            else:
                parts.append(f"{key}: {value:.2f}")
        else:
            parts.append(f"{key}: {value}")
    return " | ".join(parts)


def render_strategy_params(strategy_id: str) -> dict:
    """根据策略渲染参数调整控件"""
    params = {}

    if strategy_id == "value":
        st.subheader("价值投资策略参数")
        col1, col2 = st.columns(2)
        with col1:
            params["max_pe"] = st.number_input(
                "最大PE", min_value=1.0, max_value=100.0, value=15.0, step=1.0
            )
        with col2:
            params["max_pb"] = st.number_input(
                "最大PB", min_value=0.1, max_value=10.0, value=2.0, step=0.1
            )

    elif strategy_id == "growth":
        st.subheader("成长股策略参数")
        col1, col2 = st.columns(2)
        with col1:
            params["min_revenue_growth"] = st.number_input(
                "最小营收增长率(%)", min_value=0.0, max_value=200.0, value=20.0, step=5.0
            )
        with col2:
            params["min_profit_growth"] = st.number_input(
                "最小利润增长率(%)", min_value=0.0, max_value=200.0, value=15.0, step=5.0
            )

    elif strategy_id == "low_pe":
        st.subheader("低估值策略参数")
        params["max_pe"] = st.number_input(
            "最大PE", min_value=1.0, max_value=50.0, value=10.0, step=1.0
        )

    elif strategy_id == "momentum":
        st.subheader("动量策略参数")
        params["ma_period"] = st.selectbox(
            "均线周期", options=[5, 20, 60], index=1
        )

    return params


def main():
    """主函数"""
    st.set_page_config(
        page_title="量化选股 - 股票分析系统",
        page_icon="🔍",
        layout="wide",
    )

    init_session_state()
    repo = st.session_state.repository
    screener = StockScreener(repo)

    st.title("🔍 量化选股")
    st.markdown(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.markdown("---")

    # 策略选择
    st.subheader("📊 选择选股策略")

    strategies = StrategyRegistry.get_all_strategies()
    strategy_cols = st.columns(4)

    selected_strategy_id = st.session_state.get("selected_strategy_id", "value")

    for i, strategy in enumerate(strategies):
        with strategy_cols[i]:
            if st.button(
                f"{strategy.name}\n_{strategy.description}_",
                key=f"strategy_{strategy.id}",
                use_container_width=True,
                type="primary" if strategy.id == selected_strategy_id else "secondary",
            ):
                st.session_state.selected_strategy_id = strategy.id
                st.rerun()

    selected_strategy = StrategyRegistry.get_strategy(selected_strategy_id)

    st.markdown("---")

    # 参数调整
    params = render_strategy_params(selected_strategy_id)

    # 市场选择
    st.subheader("🌏 选择市场")
    market_col1, market_col2, market_col3 = st.columns(3)
    selected_market = st.session_state.get("selected_market", Market.A_STOCK)

    with market_col1:
        if st.button("A股", use_container_width=True, type="primary" if selected_market == Market.A_STOCK else "secondary"):
            st.session_state.selected_market = Market.A_STOCK
            st.rerun()

    with market_col2:
        if st.button("港股", use_container_width=True, type="primary" if selected_market == Market.HK_STOCK else "secondary"):
            st.session_state.selected_market = Market.HK_STOCK
            st.rerun()

    with market_col3:
        if st.button("美股", use_container_width=True, type="primary" if selected_market == Market.US_STOCK else "secondary"):
            st.session_state.selected_market = Market.US_STOCK
            st.rerun()

    st.markdown("---")

    # 开始筛选按钮
    start_col1, start_col2, start_col3 = st.columns([2, 2, 1])
    with start_col2:
        if st.button("🚀 开始选股", type="primary", use_container_width=True):
            with st.spinner("正在筛选股票..."):
                try:
                    st.session_state.screen_results = screener.screen(
                        selected_strategy_id, params, selected_market
                    )
                    st.session_state.selected_symbols = set()
                    st.rerun()
                except Exception as e:
                    st.error(f"选股失败: {str(e)}")

    st.markdown("---")

    # 显示筛选结果
    st.subheader("📋 筛选结果")

    results = st.session_state.screen_results

    if not results:
        st.info("暂无筛选结果，请调整策略参数后重新筛选")
        return

    # 统计信息
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        st.metric("筛选结果数量", len(results))

    with stat_col2:
        avg_score = sum(r.score for r in results) / len(results) if results else 0
        st.metric("平均评分", f"{avg_score:.1f}")

    with stat_col3:
        high_score_count = sum(1 for r in results if r.score >= 75)
        st.metric("高评分股票(>=75)", high_score_count)

    st.markdown("---")

    # 批量操作
    batch_col1, batch_col2 = st.columns([1, 1])
    with batch_col1:
        if st.button("📥 全部加入自选股", use_container_width=True):
            added_count = 0
            for result in results:
                try:
                    repo.add_to_watchlist(result.symbol)
                    added_count += 1
                except Exception:
                    pass  # 已存在的跳过
            if added_count > 0:
                st.success(f"已添加 {added_count} 只股票到自选股")
            else:
                st.info("所有股票已在自选股中")

    with batch_col2:
        if st.button("✅ 批量添加选中股票", use_container_width=True):
            if not st.session_state.selected_symbols:
                st.warning("请先勾选要添加的股票")
            else:
                added_count = 0
                for symbol in st.session_state.selected_symbols:
                    try:
                        repo.add_to_watchlist(symbol)
                        added_count += 1
                    except Exception:
                        pass
                if added_count > 0:
                    st.success(f"已添加 {added_count} 只股票到自选股")
                    st.session_state.selected_symbols = set()
                    st.rerun()
                else:
                    st.info("所选股票已在自选股中")

    st.markdown("---")

    # 结果表格
    for i, result in enumerate(results):
        with st.container():
            # 股票卡片
            card_col1, card_col2, card_col3, card_col4, card_col5, card_col6, card_col7 = st.columns([1.5, 2, 1.5, 2.5, 1, 1, 1])

            with card_col1:
                st.markdown(f"**#{i+1}**")

            with card_col2:
                st.markdown(f"**{result.symbol}**")
                st.caption(result.name)

            with card_col3:
                stars = render_stars(result.score)
                st.markdown(f"**{stars}**")
                st.caption(f"{result.score:.1f}分")

            with card_col4:
                details = render_match_details(result.match_details)
                st.markdown(details)

            with card_col5:
                if result.current_price:
                    st.metric("价格", f"{float(result.current_price):.2f}")
                else:
                    st.markdown("--")

            with card_col6:
                # 选择复选框
                is_selected = result.symbol in st.session_state.selected_symbols
                if st.checkbox("选择", key=f"select_{result.symbol}", value=is_selected):
                    st.session_state.selected_symbols.add(result.symbol)
                else:
                    st.session_state.selected_symbols.discard(result.symbol)

            with card_col7:
                # 单个添加按钮
                if st.button("➕加入", key=f"add_{result.symbol}"):
                    try:
                        repo.add_to_watchlist(result.symbol)
                        st.success(f"已添加 {result.symbol}")
                    except Exception:
                        st.info(f"{result.symbol} 已在自选股中")

            st.markdown("---")

    # 底部操作提示
    st.caption("提示: 点击\"选择\"复选框可批量添加股票到自选股")


if __name__ == "__main__":
    main()
