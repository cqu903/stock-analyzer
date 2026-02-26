"""
Tests for portfolio repository methods.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from src.data.repository import Repository
from src.models.portfolio import Account, AccountType, Transaction, TradeType


@pytest.fixture
def repo():
    return Repository("sqlite:///:memory:")


def test_create_and_get_account(repo):
    """测试创建和获取账户"""
    account = Account(
        name="测试账户",
        account_type=AccountType.SECURITIES,
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    created_account = repo.create_account(account)

    assert created_account.id is not None
    assert created_account.name == "测试账户"

    accounts = repo.get_accounts()
    assert len(accounts) == 1
    assert accounts[0].name == "测试账户"
    assert accounts[0].account_type == AccountType.SECURITIES


def test_get_account(repo):
    """测试获取单个账户"""
    account = Account(
        name="测试账户",
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    created = repo.create_account(account)

    fetched = repo.get_account(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "测试账户"


def test_get_nonexistent_account(repo):
    """测试获取不存在的账户"""
    result = repo.get_account(999)
    assert result is None


def test_update_account_cash(repo):
    """测试更新账户现金"""
    account = Account(
        name="测试账户",
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    created = repo.create_account(account)

    # 增加现金
    repo.update_account_cash(created.id, Decimal("5000"))
    updated = repo.get_account(created.id)
    assert updated.current_cash == Decimal("105000")

    # 减少现金
    repo.update_account_cash(created.id, Decimal("-2000"))
    updated = repo.get_account(created.id)
    assert updated.current_cash == Decimal("103000")


def test_delete_account(repo):
    """测试删除账户"""
    account = Account(
        name="测试账户",
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    created = repo.create_account(account)

    repo.delete_account(created.id)
    accounts = repo.get_accounts()
    assert len(accounts) == 0


def test_add_and_get_transactions(repo):
    """测试添加和获取交易记录"""
    # 先创建账户
    account = Account(
        name="测试账户",
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    account = repo.create_account(account)

    # 添加买入交易
    transaction = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.5"),
        amount=Decimal("10500"),
        trade_date=date.today(),
    )
    created_transaction = repo.add_transaction(transaction)

    assert created_transaction.id is not None

    transactions = repo.get_transactions(account.id)
    assert len(transactions) == 1
    assert transactions[0].symbol == "000001.SZ"
    assert transactions[0].trade_type == TradeType.BUY

    # 验证账户现金已更新
    updated_account = repo.get_account(account.id)
    assert updated_account.current_cash == Decimal("89500")  # 100000 - 10500


def test_add_sell_transaction(repo):
    """测试添加卖出交易"""
    account = Account(
        name="测试账户",
        initial_capital=Decimal("100000"),
        current_cash=Decimal("50000"),
    )
    account = repo.create_account(account)

    # 添加卖出交易
    transaction = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.SELL,
        shares=1000,
        price=Decimal("12.0"),
        amount=Decimal("12000"),
        trade_date=date.today(),
    )
    repo.add_transaction(transaction)

    # 验证账户现金增加
    updated_account = repo.get_account(account.id)
    assert updated_account.current_cash == Decimal("62000")  # 50000 + 12000


def test_get_transactions_by_symbol(repo):
    """测试获取指定股票的交易记录"""
    account = Account(
        name="测试账户",
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    account = repo.create_account(account)

    # 添加多笔交易
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
    transactions = repo.get_transactions_by_symbol(account.id, "000001.SZ")
    assert len(transactions) == 2
    assert all(t.symbol == "000001.SZ" for t in transactions)
    # 应该按日期升序排列
    assert transactions[0].trade_date == date(2025, 1, 1)
    assert transactions[1].trade_date == date(2025, 1, 15)


def test_multiple_accounts(repo):
    """测试多个账户"""
    account1 = Account(
        name="证券账户",
        account_type=AccountType.SECURITIES,
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    account2 = Account(
        name="模拟账户",
        account_type=AccountType.SIMULATION,
        initial_capital=Decimal("50000"),
        current_cash=Decimal("50000"),
    )
    repo.create_account(account1)
    repo.create_account(account2)

    accounts = repo.get_accounts()
    assert len(accounts) == 2

    # 添加交易到不同账户
    t1 = Transaction(
        account_id=accounts[0].id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=100,
        price=Decimal("10.0"),
        amount=Decimal("1000"),
        trade_date=date.today(),
    )
    t2 = Transaction(
        account_id=accounts[1].id,
        symbol="000002.SZ",
        trade_type=TradeType.BUY,
        shares=100,
        price=Decimal("20.0"),
        amount=Decimal("2000"),
        trade_date=date.today(),
    )
    repo.add_transaction(t1)
    repo.add_transaction(t2)

    # 验证交易分别属于不同账户
    transactions1 = repo.get_transactions(accounts[0].id)
    transactions2 = repo.get_transactions(accounts[1].id)

    assert len(transactions1) == 1
    assert len(transactions2) == 1
    assert transactions1[0].symbol == "000001.SZ"
    assert transactions2[0].symbol == "000002.SZ"


def test_transaction_with_fee_and_notes(repo):
    """测试带手续费和备注的交易"""
    account = Account(
        name="测试账户",
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    account = repo.create_account(account)

    transaction = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.5"),
        amount=Decimal("10500"),
        fee=Decimal("5.25"),
        trade_date=date.today(),
        notes="测试备注",
    )
    repo.add_transaction(transaction)

    transactions = repo.get_transactions(account.id)
    assert len(transactions) == 1
    assert transactions[0].fee == Decimal("5.25")
    assert transactions[0].notes == "测试备注"


def test_transactions_limit(repo):
    """测试交易记录限制"""
    account = Account(
        name="测试账户",
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    account = repo.create_account(account)

    # 添加多笔交易
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

    # 默认获取100条
    all_transactions = repo.get_transactions(account.id)
    assert len(all_transactions) == 10

    # 限制5条
    limited_transactions = repo.get_transactions(account.id, limit=5)
    assert len(limited_transactions) == 5


def test_delete_account_cascades_transactions(repo):
    """测试删除账户时交易记录也被删除"""
    account = Account(
        name="测试账户",
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    account = repo.create_account(account)

    transaction = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.5"),
        amount=Decimal("10500"),
        trade_date=date.today(),
    )
    repo.add_transaction(transaction)

    # 删除账户
    repo.delete_account(account.id)

    # 验证交易也被删除
    transactions = repo.get_transactions(account.id)
    assert len(transactions) == 0
