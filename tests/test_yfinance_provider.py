import pytest
from src.data.yfinance_provider import YFinanceProvider
from src.models.schemas import Market


@pytest.fixture
def provider():
    return YFinanceProvider()


def test_parse_symbol_us_stock(provider):
    """测试美股代码解析"""
    symbol, market = provider._parse_symbol("AAPL.US")
    assert symbol == "AAPL"
    assert market == Market.US_STOCK


def test_parse_symbol_without_suffix(provider):
    """测试无后缀代码"""
    symbol, market = provider._parse_symbol("TSLA")
    assert symbol == "TSLA"
    assert market == Market.US_STOCK
