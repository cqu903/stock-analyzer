import pytest
from datetime import date

from src.data.tushare_provider import TushareProvider
from src.models.schemas import Market


@pytest.fixture
def provider():
    return TushareProvider("test_token")


def test_parse_symbol_a_stock(provider):
    """测试A股代码解析"""
    ts_code, market = provider._parse_symbol("000001.SZ")
    assert ts_code == "000001.SZ"
    assert market == Market.A_STOCK


def test_to_stock_info(provider):
    """测试转换为StockInfo"""
    row = {
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "industry": "银行",
    }
    info = provider._to_stock_info(row)
    assert info.symbol == "000001.SZ"
    assert info.name == "平安银行"
