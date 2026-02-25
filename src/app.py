"""
Streamlit主入口
股票分析系统首页，展示概览信息和快捷功能
"""

import streamlit as st
from datetime import datetime

from config.settings import get_settings
from src.data.repository import Repository
from src.models.schemas import Market


def init_session_state():
    """初始化会话状态"""
    if "repository" not in st.session_state:
        settings = get_settings()
        # 使用SQLite作为默认数据库（测试模式）
        st.session_state.repository = Repository("sqlite:///stock_analyzer.db")


def main():
    """主函数"""
    st.set_page_config(
        page_title="股票分析系统",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()
    repo = st.session_state.repository

    # 侧边栏
    st.sidebar.title("📈 股票分析系统")
    st.sidebar.markdown("---")

    # 市场选择
    market = st.sidebar.selectbox(
        "选择市场",
        options=[Market.A_STOCK, Market.HK_STOCK, Market.US_STOCK],
        format_func=lambda x: x.value,
    )
    st.session_state.current_market = market

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 快速导航")
    st.sidebar.markdown("""
    - 📊 自选股管理
    - 📈 技术分析
    - 📄 基本面分析
    - 🔔 监控预警
    - 💬 AI助手
    """)

    # 主内容区
    st.title("📈 股票分析系统")
    st.markdown(f"**当前市场**: {market.value} | **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    st.markdown("---")

    # 概览指标
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        watchlist = repo.get_watchlist()
        st.metric(label="自选股数量", value=len(watchlist), delta=None)

    with col2:
        # 获取未读预警数量
        alerts = repo.get_alerts(limit=100)
        unread_count = sum(1 for a in alerts if not a.is_read)
        st.metric(label="未读预警", value=unread_count, delta=None)

    with col3:
        st.metric(label="支持市场", value="3", delta=None)

    with col4:
        if watchlist:
            # 获取最新行情
            latest_quote = repo.get_latest_quote(watchlist[0].symbol)
            if latest_quote:
                change = float(latest_quote.change_pct) if latest_quote.change_pct else 0
                st.metric(
                    label=f"{watchlist[0].symbol}",
                    value=f"{latest_quote.close:.2f}",
                    delta=f"{change:.2f}%",
                )
            else:
                st.metric(label="最新价格", value="--", delta=None)
        else:
            st.metric(label="最新价格", value="--", delta=None)

    st.markdown("---")

    # 快速搜索
    st.subheader("🔍 快速搜索")
    search_col1, search_col2 = st.columns([3, 1])

    with search_col1:
        search_keyword = st.text_input(
            "输入股票代码或名称",
            placeholder="例如: 000001, 平安银行, AAPL",
            label_visibility="collapsed",
        )

    with search_col2:
        search_btn = st.button("搜索", type="primary", use_container_width=True)

    if search_btn and search_keyword:
        st.info(f"正在搜索: {search_keyword}")
        # 这里可以跳转到搜索结果页面或显示结果
        st.markdown("**搜索结果将在这里显示**")

    st.markdown("---")

    # 最近预警
    st.subheader("🔔 最近预警")
    recent_alerts = repo.get_alerts(limit=5)

    if recent_alerts:
        for alert in recent_alerts:
            alert_icon = "🔴" if not alert.is_read else "⚪"
            st.markdown(
                f"""
                {alert_icon} **{alert.symbol}** - {alert.alert_type.value}
                - {alert.message}
                - *{alert.triggered_at.strftime('%Y-%m-%d %H:%M')}*
                """
            )
    else:
        st.info("暂无预警记录")

    st.markdown("---")

    # 页脚
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <small>股票分析系统 v1.0 | 数据仅供参考，不构成投资建议</small>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
