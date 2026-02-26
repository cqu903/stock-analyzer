"""测试选股引擎"""

from datetime import date
from decimal import Decimal

import pytest

from src.data.repository import Repository
from src.models.schemas import Financial, Market, StockInfo
from src.models.screening import ScreenResult
from src.screening.screener import StockScreener


@pytest.fixture
def test_repo(tmp_path):
    """创建测试数据库"""
    db_path = tmp_path / "test.db"
    repo = Repository(f"sqlite:///{db_path}")

    # 添加测试股票信息
    repo.save_stock_info(StockInfo(
        symbol="000001.SZ",
        name="平安银行",
        market=Market.A_STOCK,
        industry="银行",
        list_date=date(1991, 4, 3),
    ))
    repo.save_stock_info(StockInfo(
        symbol="600519.SH",
        name="贵州茅台",
        market=Market.A_STOCK,
        industry="白酒",
        list_date=date(2001, 8, 27),
    ))
    repo.save_stock_info(StockInfo(
        symbol="00700.HK",
        name="腾讯控股",
        market=Market.HK_STOCK,
        industry="科技",
        list_date=date(2004, 6, 16),
    ))

    # 添加财务数据 - 平安银行（价值股）
    repo.save_financials([Financial(
        symbol="000001.SZ",
        report_date=date(2026, 1, 15),
        revenue=Decimal("1000.00"),
        net_profit=Decimal("300.00"),
        total_assets=Decimal("50000.00"),
        total_equity=Decimal("4000.00"),
        roe=Decimal("7.5"),
        pe=Decimal("5.5"),
        pb=Decimal("0.8"),
        debt_ratio=Decimal("92.0"),
        gross_margin=Decimal("30.0"),
    )])

    # 添加财务数据 - 贵州茅台（高ROE，高PB）
    repo.save_financials([Financial(
        symbol="600519.SH",
        report_date=date(2026, 1, 15),
        revenue=Decimal("800.00"),
        net_profit=Decimal("400.00"),
        total_assets=Decimal("3000.00"),
        total_equity=Decimal("2000.00"),
        roe=Decimal("20.0"),
        pe=Decimal("25.0"),
        pb=Decimal("10.0"),
        debt_ratio=Decimal("25.0"),
        gross_margin=Decimal("90.0"),
    )])

    # 添加到自选股
    repo.add_to_watchlist("000001.SZ", "价值股")
    repo.add_to_watchlist("600519.SH", "成长价值")

    return repo


def test_screener_init(test_repo):
    """测试选股引擎初始化"""
    screener = StockScreener(test_repo)
    assert screener.repo == test_repo
    assert screener.fundamental_analyzer is not None
    assert screener.technical_analyzer is not None


def test_screen_value_strategy(test_repo):
    """测试价值投资策略筛选"""
    screener = StockScreener(test_repo)

    results = screener.screen(
        "value",
        {"max_pe": 15, "max_pb": 2},
        Market.A_STOCK
    )

    # 平安银行PE=5.5, PB=0.8 符合条件
    # 贵州茅台PE=25, PB=10 不符合
    assert len(results) == 1
    assert results[0].symbol == "000001.SZ"
    assert results[0].score > 0
    assert results[0].match_details["pe"] == 5.5
    assert results[0].match_details["pb"] == 0.8


def test_screen_low_pe_strategy(test_repo):
    """测试低PE策略筛选"""
    screener = StockScreener(test_repo)

    results = screener.screen(
        "low_pe",
        {"max_pe": 10},
        Market.A_STOCK
    )

    # 只有平安银行PE=5.5符合
    assert len(results) >= 1
    assert any(r.symbol == "000001.SZ" for r in results)
    for result in results:
        assert result.match_details["pe"] <= 10


def test_screen_growth_strategy_no_data(test_repo):
    """测试成长股策略 - 无足够数据"""
    screener = StockScreener(test_repo)

    results = screener.screen(
        "growth",
        {"min_revenue_growth": 20, "min_profit_growth": 15},
        Market.A_STOCK
    )

    # 没有多期财务数据，应该返回空列表
    assert len(results) == 0


def test_screen_invalid_strategy(test_repo):
    """测试无效策略ID"""
    screener = StockScreener(test_repo)

    with pytest.raises(ValueError, match="策略不存在"):
        screener.screen("invalid_strategy", {}, Market.A_STOCK)


def test_screen_empty_stock_pool(test_repo):
    """测试空股票池"""
    screener = StockScreener(test_repo)

    # 港股市场没有自选股
    results = screener.screen(
        "value",
        {},
        Market.HK_STOCK
    )

    assert len(results) == 0


def test_calculate_value_score():
    """测试价值评分计算"""
    screener = StockScreener(Repository("sqlite:///test.db"))

    # 低PE低PB应该得分高
    score1 = screener._calculate_value_score(5.0, 0.5, {"max_pe": 15, "max_pb": 2})
    score2 = screener._calculate_value_score(14.0, 1.8, {"max_pe": 15, "max_pb": 2})

    assert score1 > score2
    assert 0 <= score1 <= 100
    assert 0 <= score2 <= 100


def test_screen_results_sorted(test_repo):
    """测试筛选结果按评分排序"""
    screener = StockScreener(test_repo)

    results = screener.screen(
        "low_pe",
        {"max_pe": 30},
        Market.A_STOCK
    )

    if len(results) > 1:
        # 检查是否按评分降序排列
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score


def test_screen_result_model():
    """测试筛选结果模型"""
    result = ScreenResult(
        symbol="000001.SZ",
        name="平安银行",
        score=85.5,
        match_details={"pe": 5.5, "pb": 0.8},
        current_price=Decimal("10.50"),
    )

    assert result.symbol == "000001.SZ"
    assert result.name == "平安银行"
    assert result.score == 85.5
    assert result.match_details["pe"] == 5.5
    assert result.current_price == Decimal("10.50")


def test_get_stock_pool_filters_by_market(test_repo):
    """测试股票池按市场过滤"""
    screener = StockScreener(test_repo)

    a_stock_pool = screener._get_stock_pool(Market.A_STOCK)
    hk_stock_pool = screener._get_stock_pool(Market.HK_STOCK)

    # A股应该有2只
    assert len(a_stock_pool) == 2
    assert all(s.market == Market.A_STOCK for s in a_stock_pool)

    # 港股应该没有
    assert len(hk_stock_pool) == 0
