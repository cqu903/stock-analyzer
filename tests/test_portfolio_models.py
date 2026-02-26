import pytest
from datetime import date, datetime
from decimal import Decimal

from src.models.portfolio import (
    Account, AccountType, Transaction, TradeType,
    Position, AccountSummary
)


def test_account_creation():
    """测试账户创建"""
    account = Account(
        id=1,
        name="A股账户",
        account_type=AccountType.SECURITIES,
        initial_capital=Decimal("100000"),
        current_cash=Decimal("50000"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert account.name == "A股账户"
    assert account.initial_capital == Decimal("100000")


def test_transaction_creation():
    """测试交易记录创建"""
    transaction = Transaction(
        id=1,
        account_id=1,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.5"),
        amount=Decimal("10500"),
        fee=Decimal("5"),
        trade_date=date.today(),
    )
    assert transaction.symbol == "000001.SZ"
    assert transaction.trade_type == TradeType.BUY


def test_position_calculation():
    """测试持仓计算"""
    position = Position(
        symbol="000001.SZ",
        name="平安银行",
        shares=1000,
        avg_cost=Decimal("10.5"),
        current_price=Decimal("12.0"),
        market_value=Decimal("12000"),
        cost_value=Decimal("10500"),
        unrealized_pnl=Decimal("1500"),
        unrealized_pnl_pct=Decimal("14.29"),
    )
    assert position.unrealized_pnl_pct > 0


def test_account_summary():
    """测试账户汇总"""
    summary = AccountSummary(
        total_assets=Decimal("150000"),
        cash=Decimal("50000"),
        positions_value=Decimal("100000"),
        total_pnl=Decimal("5000"),
        total_pnl_pct=Decimal("3.33"),
        total_cost=Decimal("145000"),
    )
    assert summary.total_assets == Decimal("150000")
    assert summary.cash == Decimal("50000")
    assert summary.positions_value == Decimal("100000")
    assert summary.total_pnl == Decimal("5000")
    assert summary.total_pnl_pct == Decimal("3.33")
    assert summary.total_cost == Decimal("145000")


def test_account_summary_negative_total_assets():
    """测试账户汇总总资产不能为负数"""
    with pytest.raises(ValueError):
        AccountSummary(
            total_assets=Decimal("-1000"),
            cash=Decimal("50000"),
            positions_value=Decimal("100000"),
            total_pnl=Decimal("5000"),
            total_pnl_pct=Decimal("3.33"),
        )


def test_account_summary_negative_cash():
    """测试账户汇总现金不能为负数"""
    with pytest.raises(ValueError):
        AccountSummary(
            total_assets=Decimal("150000"),
            cash=Decimal("-1000"),
            positions_value=Decimal("100000"),
            total_pnl=Decimal("5000"),
            total_pnl_pct=Decimal("3.33"),
        )


def test_account_summary_negative_positions_value():
    """测试账户汇总持仓市值不能为负数"""
    with pytest.raises(ValueError):
        AccountSummary(
            total_assets=Decimal("150000"),
            cash=Decimal("50000"),
            positions_value=Decimal("-1000"),
            total_pnl=Decimal("5000"),
            total_pnl_pct=Decimal("3.33"),
        )


def test_account_summary_negative_total_cost():
    """测试账户汇总总成本不能为负数"""
    with pytest.raises(ValueError):
        AccountSummary(
            total_assets=Decimal("150000"),
            cash=Decimal("50000"),
            positions_value=Decimal("100000"),
            total_pnl=Decimal("5000"),
            total_pnl_pct=Decimal("3.33"),
            total_cost=Decimal("-1000"),
        )


def test_account_summary_default_total_cost():
    """测试账户汇总总成本默认值为0"""
    summary = AccountSummary(
        total_assets=Decimal("150000"),
        cash=Decimal("50000"),
        positions_value=Decimal("100000"),
        total_pnl=Decimal("5000"),
        total_pnl_pct=Decimal("3.33"),
    )
    assert summary.total_cost == Decimal("0")
