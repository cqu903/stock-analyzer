import pytest
from src.data.futu_provider import FutuProvider
from src.models.schemas import Market


@pytest.fixture
def provider():
    # 实际使用时需要运行FutuOpenD
    return FutuProvider("127.0.0.1", 11111)


def test_parse_symbol_hk_stock(provider):
    """测试港股代码解析"""
    symbol, market = provider._parse_symbol("00700.HK")
    assert symbol == "HK.00700"
    assert market == Market.HK_STOCK


def test_parse_symbol_without_suffix(provider):
    """测试无后缀代码"""
    symbol, market = provider._parse_symbol("00700")
    assert symbol == "HK.00700"
    assert market == Market.HK_STOCK
