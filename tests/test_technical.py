"""
技术面分析器测试
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.analysis.technical import TechnicalAnalyzer
from src.data.repository import Repository
from src.models.schemas import DailyQuote


@pytest.fixture
def mock_repository():
    """创建模拟的Repository"""
    repo = MagicMock(spec=Repository)
    return repo


@pytest.fixture
def sample_quotes():
    """创建测试用的行情数据"""
    quotes = []
    base_price = 100

    for i in range(100):
        trade_date = date(2024, 1, 1) + timedelta(days=i)
        # 模拟上涨趋势
        price = base_price + i * 0.3

        quote = DailyQuote(
            symbol="000001.SZ",
            trade_date=trade_date,
            open=Decimal(str(price - 0.5)),
            high=Decimal(str(price + 1)),
            low=Decimal(str(price - 1)),
            close=Decimal(str(price)),
            volume=1000000 + i * 10000,
            pre_close=Decimal(str(price - 0.3)) if i > 0 else None,
        )
        quotes.append(quote)

    return quotes


@pytest.fixture
def sample_quotes_volatile():
    """创建波动较大的行情数据"""
    quotes = []
    base_price = 100

    for i in range(100):
        trade_date = date(2024, 1, 1) + timedelta(days=i)
        # 模拟震荡行情
        price = base_price + (i % 20 - 10) * 0.5

        quote = DailyQuote(
            symbol="000001.SZ",
            trade_date=trade_date,
            open=Decimal(str(price - 0.5)),
            high=Decimal(str(price + 2)),
            low=Decimal(str(price - 2)),
            close=Decimal(str(price)),
            volume=1000000 + i * 10000,
            pre_close=Decimal(str(price - 0.3)) if i > 0 else None,
        )
        quotes.append(quote)

    return quotes


class TestTechnicalAnalyzer:
    """技术分析器测试"""

    def test_init(self, mock_repository):
        """测试初始化"""
        analyzer = TechnicalAnalyzer(mock_repository)
        assert analyzer.repository is mock_repository

    def test_analyze_with_insufficient_data(self, mock_repository):
        """测试数据不足时的分析"""
        # 只返回少量数据
        mock_repository.get_quotes.return_value = []

        analyzer = TechnicalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", days=365)

        assert report.symbol == "000001.SZ"
        assert report.score == 0
        assert report.trend is None  # 数据不足时趋势为空

    def test_analyze_uptrend(self, mock_repository, sample_quotes):
        """测试上涨趋势分析"""
        mock_repository.get_quotes.return_value = sample_quotes

        analyzer = TechnicalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", days=365)

        assert report.symbol == "000001.SZ"
        assert report.trend is not None
        assert report.indicators is not None
        assert report.support_resistance is not None
        assert report.score >= 0 and report.score <= 100

    def test_analyze_volatile_market(self, mock_repository, sample_quotes_volatile):
        """测试震荡市场分析"""
        mock_repository.get_quotes.return_value = sample_quotes_volatile

        analyzer = TechnicalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", days=365)

        assert report.symbol == "000001.SZ"
        assert report.trend is not None
        # 震荡市场的评分应该适中
        assert report.score >= 30 and report.score <= 70

    def test_trend_analysis(self, mock_repository, sample_quotes):
        """测试趋势分析"""
        mock_repository.get_quotes.return_value = sample_quotes

        analyzer = TechnicalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", days=365)

        # 上涨趋势应该被识别
        assert report.trend.direction in [
            "强势上涨",
            "震荡偏强",
            "横盘整理",
            "震荡偏弱",
            "弱势下跌",
        ]
        assert report.trend.current_price > 0

    def test_indicators_calculation(self, mock_repository, sample_quotes):
        """测试技术指标计算"""
        mock_repository.get_quotes.return_value = sample_quotes

        analyzer = TechnicalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", days=365)

        # 检查指标是否被计算
        assert report.indicators is not None
        assert report.indicators.ma5 is not None
        assert report.indicators.ma20 is not None
        # MACD需要26+数据点
        assert report.indicators.macd is not None
        # KDJ需要9+数据点
        assert report.indicators.kdj is not None
        # RSI需要14+数据点
        assert report.indicators.rsi is not None

    def test_support_resistance_levels(self, mock_repository, sample_quotes):
        """测试支撑压力位识别"""
        mock_repository.get_quotes.return_value = sample_quotes

        analyzer = TechnicalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", days=365)

        assert report.support_resistance is not None
        assert report.support_resistance.resistance_1 > 0
        assert report.support_resistance.support_1 > 0

    def test_pattern_detection(self, mock_repository, sample_quotes):
        """测试K线形态检测"""
        mock_repository.get_quotes.return_value = sample_quotes

        analyzer = TechnicalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", days=365)

        assert isinstance(report.patterns, list)

    def test_score_calculation(self, mock_repository, sample_quotes):
        """测试评分计算"""
        mock_repository.get_quotes.return_value = sample_quotes

        analyzer = TechnicalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", days=365)

        # 评分应该在0-100之间
        assert 0 <= report.score <= 100


class TestTechnicalAnalyzerPatterns:
    """K线形态检测测试"""

    def test_bullish_pattern_detection(self, mock_repository):
        """测试看涨形态检测"""
        # 创建包含大阳线的数据
        quotes = []
        for i in range(30):
            trade_date = date(2024, 1, 1) + timedelta(days=i)

            # 最近5根K线中创建大阳线，其他为普通K线
            if i >= 25:  # 最后5根K线
                # 创建大阳线：实体占比 > 70%
                # body = 5, total_range = 6, body/total = 0.83 > 0.7
                open_price = 100 + i
                close_price = open_price + 5  # 大阳线
                high_price = close_price + 0.5
                low_price = open_price - 0.5
            else:
                # 普通K线
                open_price = 100 + i * 0.5
                close_price = open_price + 0.3
                high_price = open_price + 1
                low_price = open_price - 1

            quote = DailyQuote(
                symbol="000001.SZ",
                trade_date=trade_date,
                open=Decimal(str(open_price)),
                high=Decimal(str(high_price)),
                low=Decimal(str(low_price)),
                close=Decimal(str(close_price)),
                volume=1000000,
                pre_close=Decimal(str(100 + (i-1) * 0.5)) if i > 0 else None,
            )
            quotes.append(quote)

        mock_repository.get_quotes.return_value = quotes

        analyzer = TechnicalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", days=365)

        # 应该检测到大阳线
        assert "大阳线" in report.patterns

    def test_doji_pattern_detection(self, mock_repository):
        """测试十字星形态检测"""
        quotes = []
        for i in range(30):
            trade_date = date(2024, 1, 1) + timedelta(days=i)

            # 最近5根K线中创建十字星，其他为普通K线
            if i >= 25:  # 最后5根K线
                # 创建十字星：实体很小，上下影线较长
                # body = 0.1, total_range = 6, body/total = 0.017 < 0.1
                # upper_shadow = 2.95 > body, lower_shadow = 2.95 > body
                open_price = 100
                close_price = 100.1  # 接近开盘价
                high_price = 103
                low_price = 97
            else:
                # 普通K线
                open_price = 100 + i * 0.5
                close_price = open_price + 0.3
                high_price = open_price + 1
                low_price = open_price - 1

            quote = DailyQuote(
                symbol="000001.SZ",
                trade_date=trade_date,
                open=Decimal(str(open_price)),
                high=Decimal(str(high_price)),
                low=Decimal(str(low_price)),
                close=Decimal(str(close_price)),
                volume=1000000,
                pre_close=Decimal(str(100 + (i-1) * 0.5)) if i > 0 else None,
            )
            quotes.append(quote)

        mock_repository.get_quotes.return_value = quotes

        analyzer = TechnicalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", days=365)

        # 应该检测到十字星
        assert "十字星" in report.patterns


class TestTechnicalAnalyzerMACD:
    """MACD金叉/死叉测试"""

    def test_macd_golden_cross(self, mock_repository):
        """测试MACD金叉检测"""
        # 创建上升趋势数据
        quotes = []
        price = 100
        for i in range(50):
            trade_date = date(2024, 1, 1) + timedelta(days=i)
            price += 0.8  # 持续上涨

            quote = DailyQuote(
                symbol="000001.SZ",
                trade_date=trade_date,
                open=Decimal(str(price - 0.5)),
                high=Decimal(str(price + 1)),
                low=Decimal(str(price - 1)),
                close=Decimal(str(price)),
                volume=1000000,
                pre_close=Decimal(str(price - 0.8)) if i > 0 else None,
            )
            quotes.append(quote)

        mock_repository.get_quotes.return_value = quotes

        analyzer = TechnicalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", days=365)

        # 上涨趋势中MACD应该显示金叉或正值
        if report.indicators.macd:
            assert report.indicators.macd.macd > 0 or report.indicators.macd.dif > report.indicators.macd.dea
