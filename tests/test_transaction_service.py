"""
Tests for TransactionService
"""

import pytest
from datetime import date
from decimal import Decimal

from src.data.repository import Repository
from src.models.portfolio import Account, Transaction, TradeType
from src.portfolio.transaction_service import TransactionService


@pytest.fixture
def repo():
    return Repository("sqlite:///:memory:")


@pytest.fixture
def account(repo):
    account = Account(
        name="测试账户",
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    return repo.create_account(account)


@pytest.fixture
def service(repo):
    return TransactionService(repo)


def test_add_transaction(service, account):
    """测试添加交易记录"""
    transaction = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.5"),
        amount=Decimal("10500"),
        trade_date=date.today(),
    )

    result = service.add_transaction(transaction)

    assert result.id is not None
    assert result.symbol == "000001.SZ"
    assert result.trade_type == TradeType.BUY


def test_get_transactions(service, account, repo):
    """测试获取交易记录"""
    t1 = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.0"),
        amount=Decimal("10000"),
        trade_date=date(2025, 1, 1),
    )
    t2 = Transaction(
        account_id=account.id,
        symbol="000002.SZ",
        trade_type=TradeType.BUY,
        shares=500,
        price=Decimal("20.0"),
        amount=Decimal("10000"),
        trade_date=date(2025, 1, 15),
    )
    repo.add_transaction(t1)
    repo.add_transaction(t2)

    transactions = service.get_transactions(account.id)

    assert len(transactions) == 2
    # 应该按日期降序排列
    assert transactions[0].symbol == "000002.SZ"
    assert transactions[1].symbol == "000001.SZ"


def test_get_transactions_with_limit(service, account, repo):
    """测试限制交易记录数量"""
    for i in range(10):
        transaction = Transaction(
            account_id=account.id,
            symbol=f"00000{i}.SZ",
            trade_type=TradeType.BUY,
            shares=100,
            price=Decimal("10.0"),
            amount=Decimal("1000"),
            trade_date=date.today(),
        )
        repo.add_transaction(transaction)

    transactions = service.get_transactions(account.id, limit=5)
    assert len(transactions) == 5


def test_buy_stock(service, account, repo):
    """测试买入股票"""
    result = service.buy_stock(
        account_id=account.id,
        symbol="000001.SZ",
        shares=1000,
        price=Decimal("10.5"),
    )

    assert result is True

    transactions = service.get_transactions(account.id)
    assert len(transactions) == 1
    assert transactions[0].symbol == "000001.SZ"
    assert transactions[0].trade_type == TradeType.BUY
    assert transactions[0].shares == 1000
    assert transactions[0].price == Decimal("10.5")

    # 验证账户现金已减少
    updated_account = repo.get_account(account.id)
    assert updated_account.current_cash == Decimal("89500")  # 100000 - 10500


def test_buy_stock_with_fee(service, account, repo):
    """测试带手续费的买入"""
    result = service.buy_stock(
        account_id=account.id,
        symbol="000001.SZ",
        shares=1000,
        price=Decimal("10.5"),
        fee=Decimal("5.25"),
    )

    assert result is True

    transactions = service.get_transactions(account.id)
    assert transactions[0].fee == Decimal("5.25")

    # 验证账户现金减少了金额（fee在持仓成本中计算）
    updated_account = repo.get_account(account.id)
    assert updated_account.current_cash == Decimal("89500")  # 100000 - 10500


def test_sell_stock(service, account, repo):
    """测试卖出股票"""
    result = service.sell_stock(
        account_id=account.id,
        symbol="000001.SZ",
        shares=1000,
        price=Decimal("12.0"),
    )

    assert result is True

    transactions = service.get_transactions(account.id)
    assert len(transactions) == 1
    assert transactions[0].symbol == "000001.SZ"
    assert transactions[0].trade_type == TradeType.SELL
    assert transactions[0].shares == 1000
    assert transactions[0].price == Decimal("12.0")

    # 验证账户现金增加
    updated_account = repo.get_account(account.id)
    assert updated_account.current_cash == Decimal("112000")  # 100000 + 12000


def test_sell_stock_with_fee(service, account, repo):
    """测试带手续费的卖出"""
    result = service.sell_stock(
        account_id=account.id,
        symbol="000001.SZ",
        shares=1000,
        price=Decimal("12.0"),
        fee=Decimal("6.0"),
    )

    assert result is True

    transactions = service.get_transactions(account.id)
    assert transactions[0].fee == Decimal("6.0")

    # 验证账户现金增加了金额
    updated_account = repo.get_account(account.id)
    assert updated_account.current_cash == Decimal("112000")  # 100000 + 12000


def test_get_transactions_by_symbol(service, account, repo):
    """测试获取指定股票的交易记录"""
    t1 = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.0"),
        amount=Decimal("10000"),
        trade_date=date(2025, 1, 1),
    )
    t2 = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=500,
        price=Decimal("11.0"),
        amount=Decimal("5500"),
        trade_date=date(2025, 1, 15),
    )
    t3 = Transaction(
        account_id=account.id,
        symbol="000002.SZ",
        trade_type=TradeType.BUY,
        shares=100,
        price=Decimal("20.0"),
        amount=Decimal("2000"),
        trade_date=date(2025, 1, 10),
    )
    repo.add_transaction(t1)
    repo.add_transaction(t2)
    repo.add_transaction(t3)

    # 获取000001.SZ的交易
    transactions = service.get_transactions_by_symbol(account.id, "000001.SZ")

    assert len(transactions) == 2
    assert all(t.symbol == "000001.SZ" for t in transactions)
    # 应该按日期升序排列
    assert transactions[0].trade_date == date(2025, 1, 1)
    assert transactions[1].trade_date == date(2025, 1, 15)


def test_get_transactions_by_symbol_empty(service, account):
    """测试获取没有交易记录的股票"""
    transactions = service.get_transactions_by_symbol(account.id, "000001.SZ")
    assert len(transactions) == 0


def test_multiple_buy_sell_transactions(service, account, repo):
    """测试多次买卖交易"""
    # 买入
    service.buy_stock(account.id, "000001.SZ", 1000, Decimal("10.0"))
    service.buy_stock(account.id, "000001.SZ", 500, Decimal("11.0"))

    # 卖出
    service.sell_stock(account.id, "000001.SZ", 300, Decimal("12.0"))

    transactions = service.get_transactions(account.id)
    assert len(transactions) == 3

    # 验证三种交易类型都存在
    trade_types = [t.trade_type for t in transactions]
    assert TradeType.BUY in trade_types
    assert TradeType.SELL in trade_types

    # 统计买入和卖出股数
    buy_shares = sum(t.shares for t in transactions if t.trade_type == TradeType.BUY)
    sell_shares = sum(t.shares for t in transactions if t.trade_type == TradeType.SELL)
    assert buy_shares == 1500
    assert sell_shares == 300
