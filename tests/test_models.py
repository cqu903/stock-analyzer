from datetime import date
from decimal import Decimal

import pytest

from src.models.schemas import (
    AIAnalysis,
    Alert,
    AlertType,
    DailyQuote,
    Financial,
    FundamentalReport,
    GrowthResult,
    HealthResult,
    Indicators,
    KDJResult,
    MACDResult,
    Market,
    ProfitabilityResult,
    StockInfo,
    SupportResistance,
    TechnicalReport,
    TrendResult,
    ValuationResult,
    WatchlistItem,
)


def test_stock_info():
    info = StockInfo(symbol="000001.SZ", name="平安银行", market="A股")
    assert info.symbol == "000001.SZ"
    assert info.name == "平安银行"
    assert info.market == "A股"


def test_daily_quote():
    quote = DailyQuote(
        symbol="000001.SZ",
        trade_date=date(2024, 1, 15),
        open=Decimal("10.5"),
        high=Decimal("10.8"),
        low=Decimal("10.3"),
        close=Decimal("10.6"),
        volume=1000000,
    )
    assert quote.symbol == "000001.SZ"
    assert quote.close == Decimal("10.6")


def test_daily_quote_change_pct():
    """测试涨跌幅计算"""
    quote = DailyQuote(
        symbol="000001.SZ",
        trade_date=date(2024, 1, 15),
        open=Decimal("10.5"),
        high=Decimal("10.8"),
        low=Decimal("10.3"),
        close=Decimal("10.6"),
        volume=1000000,
        pre_close=Decimal("10.0"),
    )
    # 涨幅 = (10.6 - 10.0) / 10.0 * 100 = 6%
    assert quote.change_pct == Decimal("6.0")


def test_daily_quote_change_pct_none():
    """测试无前收盘价时涨跌幅为None"""
    quote = DailyQuote(
        symbol="000001.SZ",
        trade_date=date(2024, 1, 15),
        open=Decimal("10.5"),
        high=Decimal("10.8"),
        low=Decimal("10.3"),
        close=Decimal("10.6"),
        volume=1000000,
    )
    assert quote.change_pct is None


def test_financial():
    fin = Financial(
        symbol="000001.SZ",
        report_date=date(2024, 3, 31),
        revenue=Decimal("1000000000"),
        net_profit=Decimal("100000000"),
        roe=Decimal("15.5"),
        pe=Decimal("8.2"),
    )
    assert fin.roe == Decimal("15.5")


def test_market_enum():
    """测试市场枚举"""
    assert Market.A_STOCK.value == "A股"
    assert Market.HK_STOCK.value == "港股"
    assert Market.US_STOCK.value == "美股"


def test_watchlist_item():
    """测试自选股项目"""
    item = WatchlistItem(symbol="00700.HK", notes="腾讯控股")
    assert item.symbol == "00700.HK"
    assert item.notes == "腾讯控股"
    assert item.alert_price_high is None
    assert item.alert_price_low is None


def test_alert():
    """测试预警记录"""
    alert = Alert(
        symbol="000001.SZ",
        alert_type=AlertType.PRICE_BREAK,
        message="价格突破预警阈值",
    )
    assert alert.symbol == "000001.SZ"
    assert alert.alert_type == AlertType.PRICE_BREAK
    assert alert.is_read is False
    assert alert.id is None


def test_alert_with_id():
    """测试带ID的预警记录"""
    alert = Alert(
        id=123,
        symbol="000001.SZ",
        alert_type=AlertType.MACD_GOLDEN_CROSS,
        message="MACD金叉",
    )
    assert alert.id == 123


def test_valuation_result():
    """测试估值分析结果"""
    valuation = ValuationResult(
        pe=Decimal("10.5"),
        pb=Decimal("1.2"),
        industry_avg_pe=Decimal("15.0"),
        pe_percentile=25.5,
        is_undervalued=True,
        score=80,
    )
    assert valuation.score == 80
    assert valuation.is_undervalued is True
    assert valuation.pe_percentile == 25.5


def test_profitability_result():
    """测试盈利能力分析结果"""
    profit = ProfitabilityResult(
        roe_current=Decimal("18.5"),
        roe_avg_3y=Decimal("16.0"),
        gross_margin=Decimal("35.0"),
        roe_trend="上升",
        score=75,
    )
    assert profit.roe_current == Decimal("18.5")
    assert profit.roe_avg_3y == Decimal("16.0")
    assert profit.score == 75


def test_growth_result():
    """测试成长性分析结果"""
    growth = GrowthResult(
        revenue_yoy=Decimal("15.0"),
        profit_yoy=Decimal("20.0"),
        revenue_cagr_3y=Decimal("18.5"),
        score=85,
    )
    assert growth.revenue_cagr_3y == Decimal("18.5")
    assert growth.revenue_yoy == Decimal("15.0")


def test_health_result():
    """测试财务健康度分析结果"""
    health = HealthResult(
        debt_ratio=Decimal("45.0"),
        debt_trend="稳定",
        score=70,
    )
    assert health.debt_ratio == Decimal("45.0")
    assert health.debt_trend == "稳定"


def test_fundamental_report():
    """测试基本面分析报告"""
    report = FundamentalReport(
        symbol="000001.SZ",
        valuation=ValuationResult(score=60),
        profitability=ProfitabilityResult(roe_trend="稳定", score=65),
        growth=GrowthResult(score=55),
        financial_health=HealthResult(debt_trend="稳定", score=70),
        overall_score=62,
        summary="公司基本面整体表现稳定",
    )
    assert report.symbol == "000001.SZ"
    assert report.overall_score == 62
    assert report.financial_health is not None
    assert 0 <= report.overall_score <= 100


def test_macd_result():
    """测试MACD指标结果"""
    macd = MACDResult(dif=Decimal("0.5"), dea=Decimal("0.3"), macd=Decimal("0.4"))
    assert macd.dif == Decimal("0.5")


def test_macd_golden_cross():
    """测试MACD金叉判断"""
    # 金叉条件: dif > dea 且 macd > 0
    golden = MACDResult(dif=Decimal("0.5"), dea=Decimal("0.3"), macd=Decimal("0.4"))
    assert golden.is_golden_cross() is True

    # 非金叉: macd < 0
    not_golden = MACDResult(dif=Decimal("0.5"), dea=Decimal("0.3"), macd=Decimal("-0.1"))
    assert not_golden.is_golden_cross() is False

    # 非金叉: dif < dea
    not_golden2 = MACDResult(dif=Decimal("0.2"), dea=Decimal("0.3"), macd=Decimal("0.1"))
    assert not_golden2.is_golden_cross() is False


def test_kdj_result():
    """测试KDJ指标结果"""
    kdj = KDJResult(k=Decimal("75.0"), d=Decimal("70.0"), j=Decimal("85.0"))
    assert kdj.k == Decimal("75.0")


def test_indicators():
    """测试技术指标集合"""
    indicators = Indicators(
        macd=MACDResult(dif=Decimal("0.5"), dea=Decimal("0.3"), macd=Decimal("0.4")),
        kdj=KDJResult(k=Decimal("50.0"), d=Decimal("48.0"), j=Decimal("54.0")),
        rsi=Decimal("65.5"),
        ma5=Decimal("10.5"),
        ma20=Decimal("10.0"),
        ma60=Decimal("9.5"),
    )
    assert indicators.ma5 == Decimal("10.5")
    assert indicators.rsi == Decimal("65.5")


def test_trend_result():
    """测试趋势分析结果"""
    trend = TrendResult(
        direction="上涨",
        current_price=Decimal("10.5"),
    )
    assert trend.direction == "上涨"
    assert trend.current_price == Decimal("10.5")


def test_support_resistance():
    """测试支撑压力位"""
    sr = SupportResistance(
        resistance_1=Decimal("11.0"),
        resistance_2=Decimal("11.5"),
        support_1=Decimal("10.0"),
        support_2=Decimal("9.5"),
    )
    assert sr.resistance_1 == Decimal("11.0")
    assert sr.support_1 == Decimal("10.0")
    assert sr.resistance_2 == Decimal("11.5")
    assert sr.support_2 == Decimal("9.5")


def test_support_resistance_minimal():
    """测试最小支撑压力位"""
    sr = SupportResistance(
        resistance_1=Decimal("11.0"),
        support_1=Decimal("10.0"),
    )
    assert sr.resistance_2 is None
    assert sr.support_2 is None


def test_technical_report():
    """测试技术面分析报告"""
    report = TechnicalReport(
        symbol="000001.SZ",
        trend=TrendResult(direction="上涨", current_price=Decimal("10.5")),
        patterns=["金叉", "突破均线"],
        score=72,
    )
    assert report.symbol == "000001.SZ"
    assert "金叉" in report.patterns
    assert 0 <= report.score <= 100


def test_ai_analysis():
    """测试AI分析报告"""
    analysis = AIAnalysis(
        symbol="000001.SZ",
        summary="该股票基本面良好，技术面呈上涨趋势",
        recommendation="建议关注",
        risks=["行业竞争加剧", "宏观经济波动"],
        confidence=75,
    )
    assert analysis.symbol == "000001.SZ"
    assert analysis.summary == "该股票基本面良好，技术面呈上涨趋势"
    assert analysis.recommendation == "建议关注"
    assert len(analysis.risks) == 2
    assert "行业竞争加剧" in analysis.risks


# ============== 负值验证测试 ==============


def test_valuation_result_score_negative():
    """测试估值评分不能为负数"""
    with pytest.raises(ValueError):
        ValuationResult(score=-1)


def test_profitability_result_score_negative():
    """测试盈利能力评分不能为负数"""
    with pytest.raises(ValueError):
        ProfitabilityResult(roe_trend="上升", score=-5)


def test_profitability_result_score_over_max():
    """测试盈利能力评分不能超过100"""
    with pytest.raises(ValueError):
        ProfitabilityResult(roe_trend="上升", score=101)


def test_growth_result_score_negative():
    """测试成长性评分不能为负数"""
    with pytest.raises(ValueError):
        GrowthResult(score=-10)


def test_growth_result_score_over_max():
    """测试成长性评分不能超过100"""
    with pytest.raises(ValueError):
        GrowthResult(score=150)


def test_health_result_score_negative():
    """测试健康度评分不能为负数"""
    with pytest.raises(ValueError):
        HealthResult(debt_trend="稳定", score=-1)


def test_health_result_score_over_max():
    """测试健康度评分不能超过100"""
    with pytest.raises(ValueError):
        HealthResult(debt_trend="稳定", score=101)


def test_fundamental_report_score_negative():
    """测试基本面报告综合评分不能为负数"""
    with pytest.raises(ValueError):
        FundamentalReport(
            symbol="000001.SZ",
            valuation=ValuationResult(score=60),
            profitability=ProfitabilityResult(roe_trend="稳定", score=65),
            growth=GrowthResult(score=55),
            financial_health=HealthResult(debt_trend="稳定", score=70),
            overall_score=-1,
        )


def test_fundamental_report_score_over_max():
    """测试基本面报告综合评分不能超过100"""
    with pytest.raises(ValueError):
        FundamentalReport(
            symbol="000001.SZ",
            valuation=ValuationResult(score=60),
            profitability=ProfitabilityResult(roe_trend="稳定", score=65),
            growth=GrowthResult(score=55),
            financial_health=HealthResult(debt_trend="稳定", score=70),
            overall_score=101,
        )


def test_technical_report_score_negative():
    """测试技术面报告评分不能为负数"""
    with pytest.raises(ValueError):
        TechnicalReport(
            symbol="000001.SZ",
            trend=TrendResult(direction="上涨", current_price=Decimal("10.5")),
            score=-1,
        )


def test_technical_report_score_over_max():
    """测试技术面报告评分不能超过100"""
    with pytest.raises(ValueError):
        TechnicalReport(
            symbol="000001.SZ",
            trend=TrendResult(direction="上涨", current_price=Decimal("10.5")),
            score=101,
        )


def test_ai_analysis_confidence_negative():
    """测试AI分析置信度不能为负数"""
    with pytest.raises(ValueError):
        AIAnalysis(
            symbol="000001.SZ",
            summary="测试分析",
            confidence=-1,
        )


def test_ai_analysis_confidence_over_max():
    """测试AI分析置信度不能超过100"""
    with pytest.raises(ValueError):
        AIAnalysis(
            symbol="000001.SZ",
            summary="测试分析",
            confidence=101,
        )


# ============== 枚举值验证测试 ==============


def test_market_enum_valid_values():
    """测试市场枚举的有效值"""
    assert Market.A_STOCK == "A股"
    assert Market.HK_STOCK == "港股"
    assert Market.US_STOCK == "美股"


def test_market_enum_from_string():
    """测试从字符串创建市场枚举"""
    assert Market("A股") == Market.A_STOCK
    assert Market("港股") == Market.HK_STOCK
    assert Market("美股") == Market.US_STOCK


def test_market_enum_invalid_string():
    """测试无效字符串创建市场枚举应失败"""
    with pytest.raises(ValueError):
        Market("InvalidMarket")


def test_alert_type_enum_values():
    """测试预警类型枚举值"""
    assert AlertType.PRICE_BREAK == "价格突破"
    assert AlertType.ABNORMAL_VOLATILITY == "异常波动"
    assert AlertType.VOLUME_SURGE == "成交量放大"
    assert AlertType.MACD_GOLDEN_CROSS == "MACD金叉"
    assert AlertType.MACD_DEATH_CROSS == "MACD死叉"
    assert AlertType.RSI_OVERBOUGHT == "RSI超买"
    assert AlertType.RSI_OVERSOLD == "RSI超卖"
    assert AlertType.CUSTOM == "自定义"


def test_alert_type_enum_from_string():
    """测试从字符串创建预警类型枚举"""
    assert AlertType("价格突破") == AlertType.PRICE_BREAK
    assert AlertType("MACD金叉") == AlertType.MACD_GOLDEN_CROSS
    assert AlertType("自定义") == AlertType.CUSTOM


def test_alert_type_enum_invalid_string():
    """测试无效字符串创建预警类型枚举应失败"""
    with pytest.raises(ValueError):
        AlertType("InvalidAlertType")
