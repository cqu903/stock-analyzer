from datetime import date

from src.models.schemas import (
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
    RSIResult,
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
        open=10.5,
        high=10.8,
        low=10.3,
        close=10.6,
        volume=1000000,
    )
    assert quote.symbol == "000001.SZ"
    assert quote.close == 10.6


def test_financial():
    fin = Financial(
        symbol="000001.SZ",
        report_date=date(2024, 3, 31),
        revenue=1000000000,
        net_profit=100000000,
        roe=15.5,
        pe=8.2,
    )
    assert fin.roe == 15.5


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


def test_valuation_result():
    """测试估值分析结果"""
    valuation = ValuationResult(
        pe=10.5,
        pb=1.2,
        pe_industry_avg=15.0,
        pb_industry_avg=1.8,
        valuation_level="低估",
        score=80,
    )
    assert valuation.score == 80
    assert valuation.valuation_level == "低估"


def test_profitability_result():
    """测试盈利能力分析结果"""
    profit = ProfitabilityResult(
        roe=18.5,
        gross_margin=35.0,
        net_margin=12.0,
        roe_trend="上升",
        score=75,
    )
    assert profit.roe == 18.5
    assert profit.score == 75


def test_growth_result():
    """测试成长性分析结果"""
    growth = GrowthResult(
        revenue_growth=15.0,
        profit_growth=20.0,
        cagr_3y=18.5,
        growth_level="高增长",
        score=85,
    )
    assert growth.cagr_3y == 18.5
    assert growth.growth_level == "高增长"


def test_health_result():
    """测试财务健康度分析结果"""
    health = HealthResult(
        debt_ratio=45.0,
        current_ratio=1.5,
        quick_ratio=1.2,
        health_level="健康",
        score=70,
    )
    assert health.debt_ratio == 45.0
    assert health.health_level == "健康"


def test_fundamental_report():
    """测试基本面分析报告"""
    report = FundamentalReport(
        symbol="000001.SZ",
        valuation=ValuationResult(valuation_level="合理", score=60),
        profitability=ProfitabilityResult(roe_trend="稳定", score=65),
        growth=GrowthResult(growth_level="稳定", score=55),
        health=HealthResult(health_level="健康", score=70),
        overall_score=62,
        summary="公司基本面整体表现稳定",
    )
    assert report.symbol == "000001.SZ"
    assert report.overall_score == 62
    assert 0 <= report.overall_score <= 100


def test_macd_result():
    """测试MACD指标结果"""
    macd = MACDResult(dif=0.5, dea=0.3, macd=0.4, signal="金叉")
    assert macd.dif == 0.5
    assert macd.signal == "金叉"


def test_kdj_result():
    """测试KDJ指标结果"""
    kdj = KDJResult(k=75.0, d=70.0, j=85.0, signal="超买")
    assert kdj.k == 75.0
    assert kdj.signal == "超买"


def test_rsi_result():
    """测试RSI指标结果"""
    rsi = RSIResult(rsi_6=65.0, rsi_12=60.0, rsi_24=55.0, signal="正常")
    assert rsi.rsi_6 == 65.0
    assert rsi.signal == "正常"


def test_indicators():
    """测试技术指标集合"""
    indicators = Indicators(
        macd=MACDResult(dif=0.5, dea=0.3, macd=0.4, signal="多头"),
        kdj=KDJResult(k=50.0, d=48.0, j=54.0, signal="正常"),
        ma5=10.5,
        ma20=10.0,
        ma60=9.5,
    )
    assert indicators.ma5 == 10.5
    assert indicators.macd.signal == "多头"


def test_trend_result():
    """测试趋势分析结果"""
    trend = TrendResult(
        short_term="上涨",
        medium_term="震荡",
        long_term="上涨",
        trend_strength=65,
    )
    assert trend.short_term == "上涨"
    assert trend.trend_strength == 65


def test_support_resistance():
    """测试支撑压力位"""
    sr = SupportResistance(
        support_levels=[10.0, 9.5, 9.0],
        resistance_levels=[11.0, 11.5, 12.0],
        current_price=10.5,
        nearest_support=10.0,
        nearest_resistance=11.0,
    )
    assert sr.current_price == 10.5
    assert len(sr.support_levels) == 3


def test_technical_report():
    """测试技术面分析报告"""
    report = TechnicalReport(
        symbol="000001.SZ",
        trend=TrendResult(
            short_term="上涨",
            medium_term="上涨",
            long_term="震荡",
            trend_strength=70,
        ),
        signal_summary="买入",
        score=72,
    )
    assert report.symbol == "000001.SZ"
    assert report.signal_summary == "买入"
    assert 0 <= report.score <= 100
