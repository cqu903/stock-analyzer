"""
监控预警页面
预警设置和预警历史记录
"""

from datetime import datetime

import streamlit as st

from src.data.repository import Repository
from src.models.schemas import AlertType


def init_session_state():
    """初始化会话状态"""
    if "repository" not in st.session_state:
        st.session_state.repository = Repository("sqlite:///stock_analyzer.db")


def main():
    """主函数"""
    st.set_page_config(
        page_title="监控预警 - 股票分析系统",
        page_icon="🔔",
        layout="wide",
    )

    init_session_state()
    repo = st.session_state.repository

    st.title("🔔 监控预警")
    st.markdown("---")

    # Tab切换
    tab1, tab2, tab3 = st.tabs(["预警设置", "预警历史", "系统设置"])

    # ========== 预警设置 ==========
    with tab1:
        st.subheader("⚙️ 预警规则设置")

        # 获取自选股
        watchlist = repo.get_watchlist()
        if not watchlist:
            st.info("请先添加自选股")
        else:
            # 选择股票
            selected_symbol = st.selectbox(
                "选择股票",
                options=[item.symbol for item in watchlist],
                index=0,
            )

            if selected_symbol:
                st.markdown(f"**当前设置**: {selected_symbol}")

                # 价格预警
                st.markdown("### 💰 价格预警")
                price_col1, price_col2 = st.columns(2)

                with price_col1:
                    enable_high = st.checkbox("启用价格上限预警")
                    _ = st.number_input(  # noqa: F841
                        "价格上限",
                        min_value=0.0,
                        step=0.1,
                        disabled=not enable_high,
                    )

                with price_col2:
                    enable_low = st.checkbox("启用价格下限预警")
                    _ = st.number_input(  # noqa: F841
                        "价格下限",
                        min_value=0.0,
                        step=0.1,
                        disabled=not enable_low,
                    )

                st.markdown("---")

                # 技术指标预警
                st.markdown("### 📊 技术指标预警")

                tech_col1, tech_col2 = st.columns(2)

                with tech_col1:
                    _ = st.checkbox("MACD金叉/死叉预警")  # noqa: F841
                    _ = st.checkbox("RSI超买/超卖预警")  # noqa: F841

                with tech_col2:
                    _ = st.checkbox("均线突破预警")  # noqa: F841
                    _ = st.checkbox("成交量异动预警")  # noqa: F841

                st.markdown("---")

                # 保存按钮
                if st.button("保存预警设置", type="primary"):
                    st.success(f"已保存 {selected_symbol} 的预警设置")

        st.markdown("---")

        # 快速预警规则
        st.subheader("⚡ 快速预警规则")
        st.markdown("""
        系统支持以下预警类型：

        | 预警类型 | 触发条件 |
        |---------|---------|
        | 价格突破 | 股价突破设定的上限或下限 |
        | MACD金叉 | DIF线上穿DEA线 |
        | MACD死叉 | DIF线下穿DEA线 |
        | RSI超买 | RSI指标 > 70 |
        | RSI超卖 | RSI指标 < 30 |
        | 成交量放大 | 成交量为前5日均量的2倍以上 |
        | 异常波动 | 日涨跌幅超过5% |
        """)

    # ========== 预警历史 ==========
    with tab2:
        st.subheader("📜 预警历史")

        # 筛选条件
        filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])

        with filter_col1:
            filter_symbol = st.text_input("股票代码筛选", placeholder="输入股票代码")

        with filter_col2:
            filter_type = st.selectbox(
                "预警类型",
                options=["全部"] + [t.value for t in AlertType],
            )

        with filter_col3:
            limit = st.selectbox("显示条数", options=[20, 50, 100], index=0)

        st.markdown("---")

        # 获取预警记录
        alerts = repo.get_alerts(limit=limit)

        # 应用筛选
        if filter_symbol:
            alerts = [a for a in alerts if filter_symbol.upper() in a.symbol]
        if filter_type != "全部":
            alerts = [a for a in alerts if a.alert_type.value == filter_type]

        # 显示预警记录
        if alerts:
            for alert in alerts:
                # 根据预警类型选择图标
                icon_map = {
                    AlertType.PRICE_BREAK: "💰",
                    AlertType.ABNORMAL_VOLATILITY: "📊",
                    AlertType.VOLUME_SURGE: "📈",
                    AlertType.MACD_GOLDEN_CROSS: "✨",
                    AlertType.MACD_DEATH_CROSS: "❌",
                    AlertType.RSI_OVERBOUGHT: "🔥",
                    AlertType.RSI_OVERSOLD: "❄️",
                    AlertType.CUSTOM: "📌",
                }
                icon = icon_map.get(alert.alert_type, "🔔")

                # 未读标记
                unread_badge = "🔴 " if not alert.is_read else ""

                with st.expander(
                    f"{unread_badge}{icon} {alert.symbol} - {alert.alert_type.value} | {alert.triggered_at.strftime('%Y-%m-%d %H:%M')}",
                    expanded=not alert.is_read,
                ):
                    st.markdown(f"**预警内容**: {alert.message}")
                    st.markdown(f"**触发时间**: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"**状态**: {'已读' if alert.is_read else '未读'}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("标记已读", key=f"read_{alert.id}"):
                            st.success("已标记为已读")
                    with col2:
                        if st.button("查看详情", key=f"detail_{alert.id}"):
                            st.info("跳转到股票详情页面")

            # 批量操作
            st.markdown("---")
            batch_col1, batch_col2 = st.columns(2)

            with batch_col1:
                if st.button("全部标记已读", use_container_width=True):
                    st.success("所有预警已标记为已读")

            with batch_col2:
                if st.button("清空历史记录", use_container_width=True):
                    st.warning("确定要清空所有预警记录吗？")

        else:
            st.info("暂无预警记录")

    # ========== 系统设置 ==========
    with tab3:
        st.subheader("🔧 预警系统设置")

        # 通知设置
        st.markdown("### 📬 通知设置")

        notif_col1, notif_col2 = st.columns(2)

        with notif_col1:
            _ = st.checkbox("启用邮件通知")  # noqa: F841
            _ = st.text_input(  # noqa: F841
                "邮箱地址",
                placeholder="your@email.com",
                disabled=True,
            )

        with notif_col2:
            _ = st.checkbox("启用Webhook通知")  # noqa: F841
            _ = st.text_input(  # noqa: F841
                "Webhook URL",
                placeholder="https://your-webhook-url",
                disabled=True,
            )

        st.markdown("---")

        # 扫描频率
        st.markdown("### ⏱️ 扫描频率")

        freq_col1, freq_col2 = st.columns(2)

        with freq_col1:
            _ = st.select_slider(  # noqa: F841
                "扫描间隔",
                options=[1, 5, 10, 15, 30, 60],
                value=5,
                format_func=lambda x: f"{x}分钟",
            )

        with freq_col2:
            _ = st.checkbox("仅交易时间扫描", value=True)  # noqa: F841

        st.markdown("---")

        # 静默时段
        st.markdown("### 🔇 静默时段")

        silence_col1, silence_col2 = st.columns(2)

        with silence_col1:
            _ = st.checkbox("启用静默时段")  # noqa: F841
            _ = st.time_input("开始时间", value=datetime.strptime("22:00", "%H:%M").time())  # noqa: F841

        with silence_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            _ = st.time_input("结束时间", value=datetime.strptime("08:00", "%H:%M").time())  # noqa: F841

        st.markdown("---")

        # 保存设置
        if st.button("保存系统设置", type="primary", use_container_width=True):
            st.success("系统设置已保存")


if __name__ == "__main__":
    main()
