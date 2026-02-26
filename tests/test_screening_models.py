"""测试量化选股相关数据模型"""

from decimal import Decimal

import pytest

from src.models.screening import ScreenResult, Strategy


def test_strategy_creation():
    """测试策略创建"""
    strategy = Strategy(
        id="value",
        name="价值投资",
        description="低PE、低PB、高股息",
        category="价值",
        params={
            "max_pe": 15,
            "max_pb": 2,
            "min_dividend_yield": 3,
        },
    )
    assert strategy.id == "value"
    assert strategy.name == "价值投资"
    assert strategy.description == "低PE、低PB、高股息"
    assert strategy.category == "价值"
    assert strategy.params["max_pe"] == 15
    assert strategy.params["max_pb"] == 2
    assert strategy.params["min_dividend_yield"] == 3


def test_strategy_default_params():
    """测试策略默认参数"""
    strategy = Strategy(
        id="test",
        name="测试策略",
        description="测试描述",
        category="测试",
    )
    assert strategy.params == {}


def test_screen_result_creation():
    """测试筛选结果创建"""
    result = ScreenResult(
        symbol="000001.SZ",
        name="平安银行",
        score=85.5,
        match_details={
            "pe": 8.5,
            "pb": 0.9,
            "dividend_yield": 4.2,
        },
        current_price=Decimal("12.50"),
    )
    assert result.symbol == "000001.SZ"
    assert result.name == "平安银行"
    assert result.score == 85.5
    assert result.match_details["pe"] == 8.5
    assert result.current_price == Decimal("12.50")


def test_screen_result_default_values():
    """测试筛选结果默认值"""
    result = ScreenResult(
        symbol="00700.HK",
        name="腾讯控股",
        score=90.0,
    )
    assert result.match_details == {}
    assert result.current_price is None


def test_screen_result_score_validation():
    """测试筛选结果分数验证 - 必须在0-100之间"""
    # 低于最小值
    with pytest.raises(ValueError):
        ScreenResult(
            symbol="000001.SZ",
            name="平安银行",
            score=-1,
        )

    # 高于最大值
    with pytest.raises(ValueError):
        ScreenResult(
            symbol="000001.SZ",
            name="平安银行",
            score=101,
        )


def test_screen_result_boundary_scores():
    """测试筛选结果边界值"""
    # 最小值0
    result_min = ScreenResult(
        symbol="000001.SZ",
        name="平安银行",
        score=0,
    )
    assert result_min.score == 0

    # 最大值100
    result_max = ScreenResult(
        symbol="000001.SZ",
        name="平安银行",
        score=100,
    )
    assert result_max.score == 100


def test_screen_result_score_floating_point():
    """测试筛选结果小数分数"""
    result = ScreenResult(
        symbol="AAPL",
        name="Apple Inc.",
        score=75.67,
    )
    assert result.score == 75.67
