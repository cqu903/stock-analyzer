"""测试策略注册表"""


from src.models.screening import Strategy
from src.screening.strategies import StrategyRegistry


def test_get_all_strategies():
    """测试获取所有策略"""
    strategies = StrategyRegistry.get_all_strategies()
    assert len(strategies) == 4
    assert all(isinstance(s, Strategy) for s in strategies)


def test_get_all_strategies_returns_copy():
    """测试获取所有策略返回副本"""
    strategies1 = StrategyRegistry.get_all_strategies()
    strategies2 = StrategyRegistry.get_all_strategies()
    assert strategies1 is not strategies2
    assert len(strategies1) == len(strategies2)


def test_get_strategy_value():
    """测试获取价值投资策略"""
    strategy = StrategyRegistry.get_strategy("value")
    assert strategy is not None
    assert strategy.id == "value"
    assert strategy.name == "价值投资"
    assert strategy.description == "低PE、低PB、高股息"
    assert strategy.category == "价值"
    assert strategy.params["max_pe"] == 15
    assert strategy.params["max_pb"] == 2
    assert strategy.params["min_dividend_yield"] == 3


def test_get_strategy_growth():
    """测试获取成长股策略"""
    strategy = StrategyRegistry.get_strategy("growth")
    assert strategy is not None
    assert strategy.id == "growth"
    assert strategy.name == "成长股"
    assert strategy.description == "高营收增长、高利润增长"
    assert strategy.category == "成长"
    assert strategy.params["min_revenue_growth"] == 20
    assert strategy.params["min_profit_growth"] == 15
    assert strategy.params["min_roe"] == 10


def test_get_strategy_low_pe():
    """测试获取低估值策略"""
    strategy = StrategyRegistry.get_strategy("low_pe")
    assert strategy is not None
    assert strategy.id == "low_pe"
    assert strategy.name == "低估值"
    assert strategy.description == "PE低于设定值"
    assert strategy.category == "价值"
    assert strategy.params["max_pe"] == 10


def test_get_strategy_momentum():
    """测试获取动量策略"""
    strategy = StrategyRegistry.get_strategy("momentum")
    assert strategy is not None
    assert strategy.id == "momentum"
    assert strategy.name == "动量策略"
    assert strategy.description == "股价突破均线、成交量放大"
    assert strategy.category == "技术"
    assert strategy.params["ma_period"] == 20
    assert strategy.params["volume_multiplier"] == 1.5


def test_get_strategy_nonexistent():
    """测试获取不存在的策略返回None"""
    strategy = StrategyRegistry.get_strategy("nonexistent")
    assert strategy is None


def test_preset_strategies_count():
    """测试预设策略数量"""
    strategies = StrategyRegistry.get_all_strategies()
    strategy_ids = {s.id for s in strategies}
    expected_ids = {"value", "growth", "low_pe", "momentum"}
    assert strategy_ids == expected_ids


def test_strategy_categories():
    """测试策略分类"""
    strategies = StrategyRegistry.get_all_strategies()
    categories = {s.category for s in strategies}
    assert "价值" in categories
    assert "成长" in categories
    assert "技术" in categories


def test_value_strategy_params():
    """测试价值投资策略参数完整性"""
    strategy = StrategyRegistry.get_strategy("value")
    assert "max_pe" in strategy.params
    assert "max_pb" in strategy.params
    assert "min_dividend_yield" in strategy.params


def test_growth_strategy_params():
    """测试成长股策略参数完整性"""
    strategy = StrategyRegistry.get_strategy("growth")
    assert "min_revenue_growth" in strategy.params
    assert "min_profit_growth" in strategy.params
    assert "min_roe" in strategy.params


def test_low_pe_strategy_params():
    """测试低估值策略参数完整性"""
    strategy = StrategyRegistry.get_strategy("low_pe")
    assert "max_pe" in strategy.params


def test_momentum_strategy_params():
    """测试动量策略参数完整性"""
    strategy = StrategyRegistry.get_strategy("momentum")
    assert "ma_period" in strategy.params
    assert "volume_multiplier" in strategy.params
