"""选股引擎"""

from decimal import Decimal

from loguru import logger

from src.analysis.fundamental import FundamentalAnalyzer
from src.analysis.technical import TechnicalAnalyzer
from src.data.repository import Repository
from src.models.schemas import Market, StockInfo
from src.models.screening import ScreenResult, Strategy
from src.screening.strategies import StrategyRegistry


class StockScreener:
    """选股引擎"""

    def __init__(self, repo: Repository):
        self.repo = repo
        self.fundamental_analyzer = FundamentalAnalyzer(repo)
        self.technical_analyzer = TechnicalAnalyzer(repo)

    def screen(
        self, strategy_id: str, params: dict, market: Market
    ) -> list[ScreenResult]:
        """执行选股策略"""
        strategy = StrategyRegistry.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 合并默认参数
        merged_params = {**strategy.params, **params}

        # 获取股票池（自选股）
        stocks = self._get_stock_pool(market)

        # 根据策略类型筛选
        if strategy_id == "value":
            return self._screen_value_strategy(stocks, merged_params)
        elif strategy_id == "growth":
            return self._screen_growth_strategy(stocks, merged_params)
        elif strategy_id == "low_pe":
            return self._screen_low_pe_strategy(stocks, merged_params)
        elif strategy_id == "momentum":
            return self._screen_momentum_strategy(stocks, merged_params)
        else:
            return []

    def _get_stock_pool(self, market: Market) -> list[StockInfo]:
        """获取股票池"""
        watchlist = self.repo.get_watchlist()
        stocks = []
        for item in watchlist:
            info = self.repo.get_stock_info(item.symbol)
            if info and info.market == market:
                stocks.append(info)
        return stocks

    def _screen_value_strategy(self, stocks: list[StockInfo], params: dict) -> list[ScreenResult]:
        """价值投资策略筛选"""
        results = []
        max_pe = params.get("max_pe", 15)
        max_pb = params.get("max_pb", 2)

        for stock in stocks:
            try:
                financials = self.repo.get_financials(stock.symbol, years=1)
                if not financials:
                    continue

                latest = financials[-1]
                pe = float(latest.pe) if latest.pe else None
                pb = float(latest.pb) if latest.pb else None

                if pe and pb and pe <= max_pe and pb <= max_pb:
                    score = self._calculate_value_score(pe, pb, params)
                    results.append(ScreenResult(
                        symbol=stock.symbol,
                        name=stock.name,
                        score=score,
                        match_details={"pe": pe, "pb": pb},
                        current_price=None,
                    ))
            except Exception as e:
                logger.warning(f"分析 {stock.symbol} 失败: {e}")
                continue

        return sorted(results, key=lambda x: x.score, reverse=True)

    def _calculate_value_score(self, pe: float, pb: float, params: dict) -> float:
        """计算价值投资评分"""
        max_pe = params.get("max_pe", 15)
        max_pb = params.get("max_pb", 2)
        pe_score = (1 - pe / max_pe) * 50
        pb_score = (1 - pb / max_pb) * 50
        return min(100, max(0, pe_score + pb_score))

    def _screen_growth_strategy(self, stocks: list[StockInfo], params: dict) -> list[ScreenResult]:
        """成长股策略筛选"""
        results = []
        min_revenue_growth = params.get("min_revenue_growth", 20)
        min_profit_growth = params.get("min_profit_growth", 15)

        for stock in stocks:
            try:
                report = self.fundamental_analyzer.analyze(stock.symbol, years=3)
                if not report.growth:
                    continue

                revenue_yoy = float(report.growth.revenue_yoy) if report.growth.revenue_yoy else 0
                profit_yoy = float(report.growth.profit_yoy) if report.growth.profit_yoy else 0

                if revenue_yoy >= min_revenue_growth and profit_yoy >= min_profit_growth:
                    score = (revenue_yoy + profit_yoy) / 2
                    results.append(ScreenResult(
                        symbol=stock.symbol,
                        name=stock.name,
                        score=min(100, score),
                        match_details={"revenue_yoy": revenue_yoy, "profit_yoy": profit_yoy},
                        current_price=None,
                    ))
            except Exception as e:
                logger.warning(f"分析 {stock.symbol} 失败: {e}")
                continue

        return sorted(results, key=lambda x: x.score, reverse=True)

    def _screen_low_pe_strategy(self, stocks: list[StockInfo], params: dict) -> list[ScreenResult]:
        """低PE策略筛选"""
        results = []
        max_pe = params.get("max_pe", 10)

        for stock in stocks:
            try:
                financials = self.repo.get_financials(stock.symbol, years=1)
                if not financials:
                    continue

                latest = financials[-1]
                pe = float(latest.pe) if latest.pe else None

                if pe and pe <= max_pe:
                    score = max(0, 100 - pe * 5)
                    results.append(ScreenResult(
                        symbol=stock.symbol,
                        name=stock.name,
                        score=score,
                        match_details={"pe": pe},
                        current_price=None,
                    ))
            except Exception as e:
                logger.warning(f"分析 {stock.symbol} 失败: {e}")
                continue

        return sorted(results, key=lambda x: x.score, reverse=True)

    def _screen_momentum_strategy(self, stocks: list[StockInfo], params: dict) -> list[ScreenResult]:
        """动量策略筛选"""
        results = []
        ma_period = params.get("ma_period", 20)

        for stock in stocks:
            try:
                report = self.technical_analyzer.analyze(stock.symbol, days=60)
                if not report.trend or not report.indicators:
                    continue

                quote = self.repo.get_latest_quote(stock.symbol)
                if not quote:
                    continue

                current_price = float(quote.close)

                ma_value = None
                if ma_period == 5 and report.indicators.ma5:
                    ma_value = float(report.indicators.ma5)
                elif ma_period == 20 and report.indicators.ma20:
                    ma_value = float(report.indicators.ma20)
                elif ma_period == 60 and report.indicators.ma60:
                    ma_value = float(report.indicators.ma60)

                if ma_value and current_price > ma_value:
                    score = min(100, (current_price / ma_value - 1) * 200 + 50)
                    results.append(ScreenResult(
                        symbol=stock.symbol,
                        name=stock.name,
                        score=score,
                        match_details={"current_price": current_price, f"ma{ma_period}": ma_value},
                        current_price=Decimal(str(current_price)),
                    ))
            except Exception as e:
                logger.warning(f"分析 {stock.symbol} 失败: {e}")
                continue

        return sorted(results, key=lambda x: x.score, reverse=True)
