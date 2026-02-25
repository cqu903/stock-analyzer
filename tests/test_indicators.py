"""
技术指标计算模块测试
"""

from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import pytest

from src.analysis.indicators import calc_macd, calc_rsi, calc_kdj, calc_ma, calc_bollinger_bands, calc_atr


@pytest.fixture
def sample_df():
    """创建测试用的DataFrame"""
    # 生成30天的模拟行情数据
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")

    # 模拟上涨趋势的数据
    base_price = 100
    data = {
        "open": [base_price + i * 0.5 + (i % 3 - 1) * 0.3 for i in range(30)],
        "high": [base_price + i * 0.5 + 1 for i in range(30)],
        "low": [base_price + i * 0.5 - 1 for i in range(30)],
        "close": [base_price + i * 0.5 + (i % 2 - 0.5) * 0.5 for i in range(30)],
        "volume": [1000000 + i * 10000 for i in range(30)],
    }

    df = pd.DataFrame(data, index=dates)
    return df


class TestCalcMACD:
    """MACD计算测试"""

    def test_calc_macd_basic(self, sample_df):
        """测试基本MACD计算"""
        result = calc_macd(sample_df)

        assert result is not None
        assert isinstance(result.dif, Decimal)
        assert isinstance(result.dea, Decimal)
        assert isinstance(result.macd, Decimal)

    def test_calc_macd_golden_cross(self):
        """测试金叉判断"""
        # 创建一个上升趋势的数据，应该产生金叉
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        close_prices = [100 + i * 0.8 for i in range(50)]  # 强势上涨

        df = pd.DataFrame({"close": close_prices}, index=dates)
        result = calc_macd(df)

        # 在强势上涨趋势中，MACD应该是正的
        assert result.macd > 0 or result.dif > result.dea

    def test_calc_macd_custom_params(self, sample_df):
        """测试自定义参数"""
        result = calc_macd(sample_df, fast=6, slow=12, signal=4)

        assert result is not None
        assert isinstance(result.dif, Decimal)


class TestCalcRSI:
    """RSI计算测试"""

    def test_calc_rsi_basic(self, sample_df):
        """测试基本RSI计算"""
        result = calc_rsi(sample_df)

        assert result is not None
        assert isinstance(result, Decimal)
        assert 0 <= result <= 100

    def test_calc_rsi_uptrend(self):
        """测试上涨趋势的RSI"""
        # 创建连续上涨的数据
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        close_prices = [100 + i for i in range(30)]  # 连续上涨

        df = pd.DataFrame({"close": close_prices}, index=dates)
        result = calc_rsi(df)

        # 上涨趋势中RSI应该较高
        assert result > 70

    def test_calc_rsi_downtrend(self):
        """测试下跌趋势的RSI"""
        # 创建连续下跌的数据
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        close_prices = [130 - i for i in range(30)]  # 连续下跌

        df = pd.DataFrame({"close": close_prices}, index=dates)
        result = calc_rsi(df)

        # 下跌趋势中RSI应该较低
        assert result < 30

    def test_calc_rsi_custom_period(self, sample_df):
        """测试自定义周期"""
        result = calc_rsi(sample_df, period=7)

        assert result is not None
        assert 0 <= result <= 100


class TestCalcKDJ:
    """KDJ计算测试"""

    def test_calc_kdj_basic(self, sample_df):
        """测试基本KDJ计算"""
        result = calc_kdj(sample_df)

        assert result is not None
        assert isinstance(result.k, Decimal)
        assert isinstance(result.d, Decimal)
        assert isinstance(result.j, Decimal)

    def test_calc_kdj_values_range(self, sample_df):
        """测试KDJ值范围"""
        result = calc_kdj(sample_df)

        # K和D值通常在0-100之间，J值可能超出范围
        assert 0 <= float(result.k) <= 100
        assert 0 <= float(result.d) <= 100

    def test_calc_kdj_custom_params(self, sample_df):
        """测试自定义参数"""
        result = calc_kdj(sample_df, n=5, m1=2, m2=2)

        assert result is not None


class TestCalcMA:
    """均线计算测试"""

    def test_calc_ma_basic(self, sample_df):
        """测试基本均线计算"""
        result = calc_ma(sample_df)

        assert isinstance(result, dict)
        assert 5 in result  # MA5应该存在
        assert 10 in result  # MA10应该存在

    def test_calc_ma_custom_periods(self, sample_df):
        """测试自定义周期"""
        result = calc_ma(sample_df, periods=[5, 10])

        assert 5 in result
        assert 10 in result
        assert 20 not in result

    def test_calc_ma_insufficient_data(self):
        """测试数据不足时的处理"""
        # 只有10天数据
        dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
        close_prices = [100 + i for i in range(10)]

        df = pd.DataFrame({"close": close_prices}, index=dates)
        result = calc_ma(df, periods=[5, 10, 20, 60])

        assert 5 in result
        assert 10 in result
        assert 20 not in result  # 数据不足
        assert 60 not in result  # 数据不足

    def test_calc_ma_values(self, sample_df):
        """测试均线值的正确性"""
        result = calc_ma(sample_df)

        # 验证MA5是最近5天收盘价的平均值
        expected_ma5 = sample_df["close"].tail(5).mean()
        assert abs(float(result[5]) - expected_ma5) < 0.0001


class TestCalcBollingerBands:
    """布林带计算测试"""

    def test_calc_bollinger_bands_basic(self, sample_df):
        """测试基本布林带计算"""
        result = calc_bollinger_bands(sample_df)

        assert "upper" in result
        assert "middle" in result
        assert "lower" in result

        # 上轨 > 中轨 > 下轨
        assert result["upper"] > result["middle"]
        assert result["middle"] > result["lower"]

    def test_calc_bollinger_bands_custom_params(self, sample_df):
        """测试自定义参数"""
        result = calc_bollinger_bands(sample_df, period=10, std_dev=1.5)

        assert result is not None


class TestCalcATR:
    """ATR计算测试"""

    def test_calc_atr_basic(self, sample_df):
        """测试基本ATR计算"""
        result = calc_atr(sample_df)

        assert result is not None
        assert isinstance(result, Decimal)
        assert result > 0

    def test_calc_atr_custom_period(self, sample_df):
        """测试自定义周期"""
        result = calc_atr(sample_df, period=7)

        assert result is not None
        assert result > 0
