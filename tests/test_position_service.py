"""
Tests for PositionService
"""

import pytest
from datetime import date
from decimal import Decimal

from src.data.repository import Repository
from src.models.portfolio import Account, AccountType, Position
from src.models.schemas import DailyQuote, Market, StockInfo
from src.portfolio.position_service import PositionService


@pytest.fixture
def repo():
    return Repository("sqlite:///:memory:")


@pytest.fixture
def service(repo):
    return PositionService(repo)


@pytest.fixture
def account(repo):
    account = Account(
        name="测试账户",
        account_type=AccountType.SECURITIES,
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    return repo.create_account(account)


def test_get_positions_empty(service, account):
    """测试获取空持仓列表"""
    positions = service.get_positions(account.id)
    assert len(positions) == 0


def test_calculate_position_after_buy(service, account, repo):
    """测试买入后的持仓计算"""
    from src.models.portfolio import Transaction, TradeType

    # 买入1000股，价格10.5
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

    # 添加股票信息
    stock_info = StockInfo(
        symbol="000001.SZ",
        name="平安银行",
        market=Market.A_STOCK,
        industry="银行",
        list_date=date(2020, 1, 1),
    )
    repo.save_stock_info(stock_info)

    # 添加当前价格
    quote = DailyQuote(
        symbol="000001.SZ",
        trade_date=date.today(),
        open=Decimal("11.0"),
        high=Decimal("11.5"),
        low=Decimal("10.8"),
        close=Decimal("11.2"),
        volume=1000000,
    )
    repo.save_quotes([quote])

    positions = service.get_positions(account.id)

    assert len(positions) == 1
    assert positions[0].symbol == "000001.SZ"
    assert positions[0].name == "平安银行"
    assert positions[0].shares == 1000
    assert positions[0].avg_cost == Decimal("10.5")
    assert positions[0].current_price == Decimal("11.2")
    assert positions[0].market_value == Decimal("11200")
    assert positions[0].cost_value == Decimal("10500")
    assert positions[0].unrealized_pnl == Decimal("700")
    assert positions[0].unrealized_pnl_pct == Decimal("6.666666666666666666666666667")


def test_calculate_position_multiple_buys(service, account, repo):
    """测试多次买入后的持仓计算"""
    from src.models.portfolio import Transaction, TradeType

    # 第一次买入
    t1 = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.0"),
        amount=Decimal("10000"),
        trade_date=date(2025, 1, 1),
    )
    # 第二次买入
    t2 = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=500,
        price=Decimal("11.0"),
        amount=Decimal("5500"),
        trade_date=date(2025, 1, 15),
    )
    repo.add_transaction(t1)
    repo.add_transaction(t2)

    # 添加股票信息
    stock_info = StockInfo(
        symbol="000001.SZ",
        name="平安银行",
        market=Market.A_STOCK,
        industry="银行",
        list_date=date(2020, 1, 1),
    )
    repo.save_stock_info(stock_info)

    # 添加当前价格
    quote = DailyQuote(
        symbol="000001.SZ",
        trade_date=date.today(),
        open=Decimal("11.0"),
        high=Decimal("11.5"),
        low=Decimal("10.8"),
        close=Decimal("12.0"),
        volume=1000000,
    )
    repo.save_quotes([quote])

    positions = service.get_positions(account.id)

    assert len(positions) == 1
    assert positions[0].shares == 1500
    # 平均成本 = (10000 + 5500) / 1500 = 10.333...
    assert positions[0].cost_value == Decimal("15500")
    # 平均成本约等于 10.33
    assert positions[0].avg_cost > Decimal("10.33")
    assert positions[0].avg_cost < Decimal("10.34")
    assert positions[0].current_price == Decimal("12.0")
    assert positions[0].market_value == Decimal("18000")
    assert positions[0].unrealized_pnl == Decimal("2500")


def test_calculate_position_after_sell(service, account, repo):
    """测试卖出后的持仓计算"""
    from src.models.portfolio import Transaction, TradeType

    # 买入
    t1 = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.0"),
        amount=Decimal("10000"),
        trade_date=date(2025, 1, 1),
    )
    # 卖出300股
    t2 = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.SELL,
        shares=300,
        price=Decimal("12.0"),
        amount=Decimal("3600"),
        trade_date=date(2025, 1, 15),
    )
    repo.add_transaction(t1)
    repo.add_transaction(t2)

    # 添加股票信息
    stock_info = StockInfo(
        symbol="000001.SZ",
        name="平安银行",
        market=Market.A_STOCK,
        industry="银行",
        list_date=date(2020, 1, 1),
    )
    repo.save_stock_info(stock_info)

    # 添加当前价格
    quote = DailyQuote(
        symbol="000001.SZ",
        trade_date=date.today(),
        open=Decimal("11.0"),
        high=Decimal("11.5"),
        low=Decimal("10.8"),
        close=Decimal("11.5"),
        volume=1000000,
    )
    repo.save_quotes([quote])

    positions = service.get_positions(account.id)

    assert len(positions) == 1
    assert positions[0].shares == 700  # 1000 - 300
    # 卖出后成本 = 10000 - (10000/1000*300) = 7000
    assert positions[0].cost_value == Decimal("7000")
    assert positions[0].avg_cost == Decimal("10.0")
    assert positions[0].current_price == Decimal("11.5")
    assert positions[0].market_value == Decimal("8050")


def test_calculate_position_sell_all(service, account, repo):
    """测试全部卖出后无持仓"""
    from src.models.portfolio import Transaction, TradeType

    # 买入
    t1 = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.0"),
        amount=Decimal("10000"),
        trade_date=date(2025, 1, 1),
    )
    # 全部卖出
    t2 = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.SELL,
        shares=1000,
        price=Decimal("12.0"),
        amount=Decimal("12000"),
        trade_date=date(2025, 1, 15),
    )
    repo.add_transaction(t1)
    repo.add_transaction(t2)

    positions = service.get_positions(account.id)

    assert len(positions) == 0


def test_multiple_positions(service, account, repo):
    """测试多只股票持仓"""
    from src.models.portfolio import Transaction, TradeType

    # 买入不同股票
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
        trade_date=date(2025, 1, 5),
    )
    t3 = Transaction(
        account_id=account.id,
        symbol="000003.SZ",
        trade_type=TradeType.BUY,
        shares=200,
        price=Decimal("15.0"),
        amount=Decimal("3000"),
        trade_date=date(2025, 1, 10),
    )
    repo.add_transaction(t1)
    repo.add_transaction(t2)
    repo.add_transaction(t3)

    # 添加股票信息
    for symbol, name in [
        ("000001.SZ", "平安银行"),
        ("000002.SZ", "万科A"),
        ("000003.SZ", "国农科技"),
    ]:
        stock_info = StockInfo(
            symbol=symbol,
            name=name,
            market=Market.A_STOCK,
            industry="测试",
            list_date=date(2020, 1, 1),
        )
        repo.save_stock_info(stock_info)

    # 添加当前价格
    for symbol, price in [
        ("000001.SZ", Decimal("11.0")),
        ("000002.SZ", Decimal("22.0")),
        ("000003.SZ", Decimal("14.0")),
    ]:
        quote = DailyQuote(
            symbol=symbol,
            trade_date=date.today(),
            open=price,
            high=price,
            low=price,
            close=price,
            volume=1000000,
        )
        repo.save_quotes([quote])

    positions = service.get_positions(account.id)

    assert len(positions) == 3
    symbols = {p.symbol for p in positions}
    assert symbols == {"000001.SZ", "000002.SZ", "000003.SZ"}


def test_get_account_summary(service, account, repo):
    """测试获取账户汇总"""
    from src.models.portfolio import Transaction, TradeType

    # 买入股票
    t1 = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.0"),
        amount=Decimal("10000"),
        trade_date=date(2025, 1, 1),
    )
    repo.add_transaction(t1)

    # 添加股票信息和价格
    stock_info = StockInfo(
        symbol="000001.SZ",
        name="平安银行",
        market=Market.A_STOCK,
        industry="银行",
        list_date=date(2020, 1, 1),
    )
    repo.save_stock_info(stock_info)

    quote = DailyQuote(
        symbol="000001.SZ",
        trade_date=date.today(),
        open=Decimal("11.0"),
        high=Decimal("11.5"),
        low=Decimal("10.8"),
        close=Decimal("11.0"),
        volume=1000000,
    )
    repo.save_quotes([quote])

    summary = service.get_account_summary(account.id)

    assert summary.cash == Decimal("90000")  # 100000 - 10000
    assert summary.positions_value == Decimal("11000")  # 1000 * 11.0
    assert summary.total_assets == Decimal("101000")  # 90000 + 11000
    assert summary.total_cost == Decimal("10000")
    assert summary.total_pnl == Decimal("1000")
    assert summary.total_pnl_pct == Decimal("10.0")


def test_get_account_summary_empty_positions(service, account):
    """测试空持仓的账户汇总"""
    summary = service.get_account_summary(account.id)

    assert summary.cash == Decimal("100000")
    assert summary.positions_value == Decimal("0")
    assert summary.total_assets == Decimal("100000")
    assert summary.total_cost == Decimal("0")
    assert summary.total_pnl == Decimal("0")
    assert summary.total_pnl_pct == Decimal("0")


def test_get_account_summary_nonexistent_account(service):
    """测试获取不存在账户的汇总"""
    with pytest.raises(ValueError, match="账户不存在"):
        service.get_account_summary(999)


def test_position_with_no_quote(service, account, repo):
    """测试没有行情数据的持仓"""
    from src.models.portfolio import Transaction, TradeType

    transaction = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.0"),
        amount=Decimal("10000"),
        trade_date=date.today(),
    )
    repo.add_transaction(transaction)

    # 添加股票信息但无行情数据
    stock_info = StockInfo(
        symbol="000001.SZ",
        name="平安银行",
        market=Market.A_STOCK,
        industry="银行",
        list_date=date(2020, 1, 1),
    )
    repo.save_stock_info(stock_info)

    positions = service.get_positions(account.id)

    assert len(positions) == 1
    # 没有行情数据时，当前价格为0
    assert positions[0].current_price == Decimal("0")
    assert positions[0].market_value == Decimal("0")
    assert positions[0].unrealized_pnl == Decimal("-10000")  # 0 - 10000
