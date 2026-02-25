from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.data.repository import Repository
from src.models.schemas import DailyQuote, Market, StockInfo


@pytest.fixture
def repo():
    # 使用内存SQLite测试
    return Repository("sqlite:///:memory:")


def test_save_and_get_stock_info(repo):
    info = StockInfo(symbol="000001.SZ", name="平安银行", market=Market.A_STOCK)
    repo.save_stock_info(info)

    result = repo.get_stock_info("000001.SZ")
    assert result is not None
    assert result.name == "平安银行"


def test_save_and_get_quotes(repo):
    # 使用最近的日期，确保在days=30的范围内
    today = date.today()
    quotes = [
        DailyQuote(
            symbol="000001.SZ",
            trade_date=today - timedelta(days=2),
            open=Decimal("10.4"),
            high=Decimal("10.6"),
            low=Decimal("10.3"),
            close=Decimal("10.5"),
            volume=1000,
        ),
        DailyQuote(
            symbol="000001.SZ",
            trade_date=today - timedelta(days=1),
            open=Decimal("10.5"),
            high=Decimal("10.7"),
            low=Decimal("10.4"),
            close=Decimal("10.6"),
            volume=1100,
        ),
    ]
    repo.save_quotes(quotes)

    result = repo.get_quotes("000001.SZ", days=30)
    assert len(result) == 2
    assert result[-1].close == Decimal("10.6")
