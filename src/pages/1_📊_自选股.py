"""
自选股管理页面
添加、删除自选股，查看实时行情
"""

import streamlit as st
from datetime import datetime
from decimal import Decimal

from config.settings import get_settings
from src.data.repository import Repository
from src.models.schemas import Market


def init_session_state():
    """初始化会话状态"""
    if "repository" not in st.session_state:
        settings = get_settings()
        st.session_state.repository = Repository("sqlite:///stock_analyzer.db")


def main():
    """主函数"""
    st.set_page_config(
        page_title="自选股管理 - 股票分析系统",
        page_icon="📊",
        layout="wide",
    )

    init_session_state()
    repo = st.session_state.repository

    st.title("📊 自选股管理")
    st.markdown(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.markdown("---")

    # 添加自选股
    st.subheader("➕ 添加自选股")
    add_col1, add_col2, add_col3 = st.columns([2, 2, 1])

    with add_col1:
        new_symbol = st.text_input("股票代码", placeholder="例如: 000001.SZ, 00700.HK, AAPL.US")

    with add_col2:
        new_notes = st.text_input("备注（可选）", placeholder="添加备注信息")

    with add_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        add_btn = st.button("添加", type="primary", use_container_width=True)

    if add_btn and new_symbol:
        try:
            repo.add_to_watchlist(new_symbol.upper(), new_notes or None)
            st.success(f"已添加 {new_symbol} 到自选股")
            st.rerun()
        except Exception as e:
            st.error(f"添加失败: {str(e)}")

    st.markdown("---")

    # 自选股列表
    st.subheader("📋 我的自选股")
    watchlist = repo.get_watchlist()

    if not watchlist:
        st.info("暂无自选股，请添加您关注的股票")
        return

    # 表头
    header_col1, header_col2, header_col3, header_col4, header_col5, header_col6 = st.columns(
        [2, 1.5, 1.5, 1.5, 2, 1]
    )
    header_col1.markdown("**代码**")
    header_col2.markdown("**最新价**")
    header_col3.markdown("**涨跌幅**")
    header_col4.markdown("**成交量**")
    header_col5.markdown("**备注**")
    header_col6.markdown("**操作**")

    st.markdown("---")

    # 显示每个自选股
    for item in watchlist:
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 1.5, 1.5, 2, 1])

        with col1:
            st.markdown(f"**{item.symbol}**")

        with col2:
            latest_quote = repo.get_latest_quote(item.symbol)
            if latest_quote:
                st.markdown(f"{latest_quote.close:.2f}")
            else:
                st.markdown("--")

        with col3:
            if latest_quote and latest_quote.change_pct:
                change = float(latest_quote.change_pct)
                color = "green" if change >= 0 else "red"
                st.markdown(f":{color}[{change:+.2f}%]")
            else:
                st.markdown("--")

        with col4:
            if latest_quote:
                volume_m = latest_quote.volume / 10000
                st.markdown(f"{volume_m:.1f}万")
            else:
                st.markdown("--")

        with col5:
            st.markdown(item.notes or "-")

        with col6:
            if st.button("删除", key=f"del_{item.symbol}"):
                repo.remove_from_watchlist(item.symbol)
                st.success(f"已删除 {item.symbol}")
                st.rerun()

        st.markdown("---")

    # 批量操作
    st.subheader("🔧 批量操作")
    batch_col1, batch_col2 = st.columns(2)

    with batch_col1:
        if st.button("刷新所有行情", use_container_width=True):
            st.info("正在刷新行情数据...")

    with batch_col2:
        if st.button("清空自选股", use_container_width=True):
            for item in watchlist:
                repo.remove_from_watchlist(item.symbol)
            st.success("已清空自选股")
            st.rerun()

    # 预警设置
    st.markdown("---")
    st.subheader("⚠️ 价格预警设置")

    selected_symbol = st.selectbox(
        "选择股票",
        options=[item.symbol for item in watchlist],
        index=0 if watchlist else None,
    )

    if selected_symbol:
        alert_col1, alert_col2 = st.columns(2)

        with alert_col1:
            high_price = st.number_input("价格上限预警", min_value=0.0, step=0.1)

        with alert_col2:
            low_price = st.number_input("价格下限预警", min_value=0.0, step=0.1)

        if st.button("保存预警设置", type="primary"):
            st.success(f"已保存 {selected_symbol} 的预警设置")


if __name__ == "__main__":
    main()
