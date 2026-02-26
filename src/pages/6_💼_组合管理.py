"""
组合管理页面
账户管理、持仓查询、交易记录
"""

from datetime import date, datetime
from decimal import Decimal

import streamlit as st

from src.data.repository import Repository
from src.models.portfolio import AccountType, TradeType
from src.portfolio.account_manager import AccountManager
from src.portfolio.position_service import PositionService
from src.portfolio.transaction_service import TransactionService


def init_session_state():
    """初始化会话状态"""
    if "repository" not in st.session_state:
        st.session_state.repository = Repository("sqlite:///stock_analyzer.db")

    if "account_manager" not in st.session_state:
        repo = st.session_state.repository
        st.session_state.account_manager = AccountManager(repo)
        st.session_state.position_service = PositionService(repo)
        st.session_state.transaction_service = TransactionService(repo)


def main():
    """主函数"""
    st.set_page_config(
        page_title="组合管理 - 股票分析系统",
        page_icon="💼",
        layout="wide",
    )

    init_session_state()
    account_manager = st.session_state.account_manager
    position_service = st.session_state.position_service
    transaction_service = st.session_state.transaction_service

    st.title("💼 组合管理")
    st.markdown(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.markdown("---")

    # 获取所有账户
    accounts = account_manager.get_accounts()

    # 账户选择和创建
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

    with col1:
        account_options = {acc.name: acc.id for acc in accounts}
        if account_options:
            selected_account_name = st.selectbox(
                "选择账户",
                options=list(account_options.keys()),
                label_visibility="collapsed",
            )
            selected_account_id = account_options[selected_account_name]
        else:
            selected_account_name = None
            selected_account_id = None

    with col2:
        with st.expander("➕ 创建新账户", expanded=False):
            new_account_name = st.text_input("账户名称", placeholder="例如: 我的证券账户", key="new_account_name")
            account_type = st.selectbox(
                "账户类型",
                options=[AccountType.SECURITIES, AccountType.SIMULATION],
                format_func=lambda x: x.value,
                key="account_type",
            )
            initial_capital = st.number_input(
                "初始资金",
                min_value=0.0,
                step=1000.0,
                value=10000.0,
                key="initial_capital",
            )

            if st.button("创建账户", type="primary", use_container_width=True):
                if new_account_name:
                    try:
                        account_manager.create_account(
                            name=new_account_name,
                            initial_capital=Decimal(str(initial_capital)),
                            account_type=account_type,
                        )
                        st.success(f"已创建账户: {new_account_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"创建失败: {str(e)}")
                else:
                    st.warning("请输入账户名称")

    with col3:
        if selected_account_id and st.button("删除账户", type="secondary", use_container_width=True):
            try:
                account_manager.delete_account(selected_account_id)
                st.success("已删除账户")
                st.rerun()
            except Exception as e:
                st.error(f"删除失败: {str(e)}")

    with col4:
        if selected_account_id:
            account = account_manager.get_account(selected_account_id)
            if account:
                st.info(f"类型: {account.account_type.value}")

    st.markdown("---")

    # 如果没有账户，显示提示
    if not accounts:
        st.info("暂无账户，请先创建账户")
        return

    # 账户概览
    st.subheader("📊 账户概览")
    try:
        summary = position_service.get_account_summary(selected_account_id)
    except ValueError:
        st.error("获取账户信息失败")
        return

    # 概览卡片
    overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)

    with overview_col1:
        st.metric(
            "总资产",
            f"¥{Decimal(str(summary.total_assets)):,.2f}",
        )

    with overview_col2:
        st.metric(
            "现金",
            f"¥{Decimal(str(summary.cash)):,.2f}",
        )

    with overview_col3:
        st.metric(
            "持仓市值",
            f"¥{Decimal(str(summary.positions_value)):,.2f}",
        )

    with overview_col4:
        pnl_color = "normal" if summary.total_pnl >= 0 else "inverse"
        st.metric(
            "总盈亏",
            f"¥{Decimal(str(summary.total_pnl)):,.2f} ({Decimal(str(summary.total_pnl_pct)):+.2f}%)",
            delta_color=pnl_color,
        )

    st.markdown("---")

    # 持仓列表
    st.subheader("📋 持仓列表")
    positions = position_service.get_positions(selected_account_id)

    if not positions:
        st.info("暂无持仓")
    else:
        # 表头
        pos_col1, pos_col2, pos_col3, pos_col4, pos_col5, pos_col6, pos_col7 = st.columns(
            [2, 3, 2, 2, 3, 3, 2]
        )
        pos_col1.markdown("**代码**")
        pos_col2.markdown("**名称**")
        pos_col3.markdown("**持仓**")
        pos_col4.markdown("**成本价**")
        pos_col5.markdown("**现价**")
        pos_col6.markdown("**市值**")
        pos_col7.markdown("**盈亏**")

        st.markdown("---")

        # 显示每个持仓
        for pos in positions:
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 3, 2, 2, 3, 3, 2])

            with col1:
                st.markdown(f"**{pos.symbol}**")

            with col2:
                st.markdown(pos.name)

            with col3:
                st.markdown(f"{pos.shares:,}")

            with col4:
                st.markdown(f"¥{Decimal(str(pos.avg_cost)):.2f}")

            with col5:
                st.markdown(f"¥{Decimal(str(pos.current_price)):.2f}")

            with col6:
                st.markdown(f"¥{Decimal(str(pos.market_value)):,.2f}")

            with col7:
                pnl = Decimal(str(pos.unrealized_pnl))
                pnl_pct = Decimal(str(pos.unrealized_pnl_pct))
                color = "green" if pnl >= 0 else "red"
                st.markdown(f":{color}[¥{pnl:,.2f} ({pnl_pct:+.2f}%)]")

            st.markdown("---")

    st.markdown("---")

    # 添加交易
    st.subheader("➕ 添加交易")

    with st.expander("买入/卖出股票", expanded=False):
        trade_col1, trade_col2, trade_col3 = st.columns(3)

        with trade_col1:
            trade_type = st.selectbox(
                "交易类型",
                options=[TradeType.BUY, TradeType.SELL],
                format_func=lambda x: x.value,
            )

            symbol = st.text_input("股票代码", placeholder="例如: 000001.SZ, 00700.HK, AAPL")

        with trade_col2:
            shares = st.number_input("成交数量", min_value=1, step=100, value=100)
            price = st.number_input("成交价格", min_value=0.01, step=0.01, value=10.0)

        with trade_col3:
            fee = st.number_input("手续费", min_value=0.0, step=0.1, value=5.0)
            trade_date = st.date_input("交易日期", value=date.today())

        if st.button("提交交易", type="primary", use_container_width=True):
            if not symbol:
                st.warning("请输入股票代码")
            else:
                try:
                    if trade_type == TradeType.BUY:
                        success = transaction_service.buy_stock(
                            account_id=selected_account_id,
                            symbol=symbol.upper(),
                            shares=shares,
                            price=Decimal(str(price)),
                            fee=Decimal(str(fee)),
                        )
                    else:
                        success = transaction_service.sell_stock(
                            account_id=selected_account_id,
                            symbol=symbol.upper(),
                            shares=shares,
                            price=Decimal(str(price)),
                            fee=Decimal(str(fee)),
                        )

                    if success:
                        st.success(f"交易成功: {trade_type.value} {symbol.upper()} {shares}股")
                        st.rerun()
                    else:
                        st.error("交易失败")
                except Exception as e:
                    st.error(f"交易失败: {str(e)}")

    st.markdown("---")

    # 交易历史
    st.subheader("📜 交易历史")
    transactions = transaction_service.get_transactions(selected_account_id, limit=50)

    if not transactions:
        st.info("暂无交易记录")
    else:
        # 表头
        tx_col1, tx_col2, tx_col3, tx_col4, tx_col5, tx_col6, tx_col7 = st.columns(
            [2, 1.5, 2, 2, 3, 2, 2]
        )
        tx_col1.markdown("**日期**")
        tx_col2.markdown("**类型**")
        tx_col3.markdown("**代码**")
        tx_col4.markdown("**数量**")
        tx_col5.markdown("**价格**")
        tx_col6.markdown("**金额**")
        tx_col7.markdown("**手续费**")

        st.markdown("---")

        # 显示每笔交易
        for tx in reversed(transactions):  # 最新的在前
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1.5, 2, 2, 3, 2, 2])

            with col1:
                st.markdown(tx.trade_date.strftime("%Y-%m-%d"))

            with col2:
                type_color = "red" if tx.trade_type == TradeType.BUY else "green"
                st.markdown(f":{type_color}[{tx.trade_type.value}]")

            with col3:
                st.markdown(f"**{tx.symbol}**")

            with col4:
                st.markdown(f"{tx.shares:,}")

            with col5:
                st.markdown(f"¥{Decimal(str(tx.price)):.2f}")

            with col6:
                st.markdown(f"¥{Decimal(str(tx.amount)):,.2f}")

            with col7:
                st.markdown(f"¥{Decimal(str(tx.fee)):.2f}")

            st.markdown("---")


if __name__ == "__main__":
    main()
