"""
Tests for AccountManager
"""

import pytest
from decimal import Decimal

from src.data.repository import Repository
from src.models.portfolio import Account, AccountType
from src.portfolio.account_manager import AccountManager


@pytest.fixture
def repo():
    return Repository("sqlite:///:memory:")


@pytest.fixture
def manager(repo):
    return AccountManager(repo)


def test_create_account(manager):
    """测试创建账户"""
    account = manager.create_account(
        name="测试账户",
        initial_capital=Decimal("100000"),
    )

    assert account.id is not None
    assert account.name == "测试账户"
    assert account.account_type == AccountType.SECURITIES
    assert account.initial_capital == Decimal("100000")
    assert account.current_cash == Decimal("100000")


def test_create_account_with_type(manager):
    """测试创建不同类型的账户"""
    account = manager.create_account(
        name="模拟账户",
        initial_capital=Decimal("50000"),
        account_type=AccountType.SIMULATION,
    )

    assert account.name == "模拟账户"
    assert account.account_type == AccountType.SIMULATION


def test_create_multiple_accounts(manager):
    """测试创建多个账户"""
    account1 = manager.create_account(
        name="证券账户",
        initial_capital=Decimal("100000"),
    )
    account2 = manager.create_account(
        name="模拟账户",
        initial_capital=Decimal("50000"),
    )

    assert account1.id != account2.id

    accounts = manager.get_accounts()
    assert len(accounts) == 2


def test_get_accounts(manager):
    """测试获取所有账户"""
    manager.create_account("账户1", Decimal("100000"))
    manager.create_account("账户2", Decimal("50000"))
    manager.create_account("账户3", Decimal("200000"))

    accounts = manager.get_accounts()
    assert len(accounts) == 3
    account_names = [a.name for a in accounts]
    assert "账户1" in account_names
    assert "账户2" in account_names
    assert "账户3" in account_names


def test_get_accounts_empty(manager):
    """测试获取空账户列表"""
    accounts = manager.get_accounts()
    assert len(accounts) == 0


def test_get_account(manager):
    """测试获取单个账户"""
    created = manager.create_account("测试账户", Decimal("100000"))

    fetched = manager.get_account(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "测试账户"


def test_get_nonexistent_account(manager):
    """测试获取不存在的账户"""
    result = manager.get_account(999)
    assert result is None


def test_delete_account(manager):
    """测试删除账户"""
    account = manager.create_account("待删除账户", Decimal("100000"))
    account_id = account.id

    result = manager.delete_account(account_id)
    assert result is True

    # 验证账户已删除
    deleted = manager.get_account(account_id)
    assert deleted is None

    accounts = manager.get_accounts()
    assert len(accounts) == 0


def test_delete_account_with_transactions(manager, repo):
    """测试删除有交易记录的账户"""
    from src.models.portfolio import Transaction, TradeType
    from datetime import date

    account = manager.create_account("测试账户", Decimal("100000"))

    # 添加交易记录
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
    manager.delete_account(account.id)

    # 验证账户和交易都被删除
    accounts = manager.get_accounts()
    assert len(accounts) == 0

    transactions = repo.get_transactions(account.id)
    assert len(transactions) == 0
