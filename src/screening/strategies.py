"""策略注册表"""

from src.models.screening import Strategy


class StrategyRegistry:
    """策略注册表，内置预设策略"""

    _strategies: list[Strategy] = [
        Strategy(
            id="value",
            name="价值投资",
            description="低PE、低PB、高股息",
            category="价值",
            params={
                "max_pe": 15,
                "max_pb": 2,
                "min_dividend_yield": 3,
            },
        ),
        Strategy(
            id="growth",
            name="成长股",
            description="高营收增长、高利润增长",
            category="成长",
            params={
                "min_revenue_growth": 20,
                "min_profit_growth": 15,
                "min_roe": 10,
            },
        ),
        Strategy(
            id="low_pe",
            name="低估值",
            description="PE低于设定值",
            category="价值",
            params={
                "max_pe": 10,
            },
        ),
        Strategy(
            id="momentum",
            name="动量策略",
            description="股价突破均线、成交量放大",
            category="技术",
            params={
                "ma_period": 20,
                "volume_multiplier": 1.5,
            },
        ),
    ]

    @classmethod
    def get_all_strategies(cls) -> list[Strategy]:
        """获取所有策略"""
        return cls._strategies.copy()

    @classmethod
    def get_strategy(cls, strategy_id: str) -> Strategy | None:
        """获取指定策略"""
        for strategy in cls._strategies:
            if strategy.id == strategy_id:
                return strategy
        return None
