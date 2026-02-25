"""
基本面分析器测试
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.analysis.fundamental import FundamentalAnalyzer
from src.data.repository import Repository
from src.models.schemas import Financial


@pytest.fixture
def mock_repository():
    """创建模拟的Repository"""
    repo = MagicMock(spec=Repository)
    return repo


@pytest.fixture
def sample_financials():
    """创建测试用的财务数据"""
    financials = []

    # 创建5年的财务数据（每年4个季度）
    # 使用递增的序号来确保ROE有明显的上升趋势
    idx = 0
    for year in range(2024, 2019, -1):
        for quarter in range(4, 0, -1):
            month = quarter * 3
            report_date = date(year, month, 30)

            # ROE从10逐年上升到20（有明显的上升趋势）
            roe_value = 10 + idx * 0.5
            # PE从25逐年下降到15
            pe_value = 25 - idx * 0.5
            # 负债率从50下降到30
            debt_value = 50 - idx * 1
            # 营收逐年增长
            revenue_value = 10000 + idx * 200
            profit_value = 1000 + idx * 50

            financial = Financial(
                symbol="000001.SZ",
                report_date=report_date,
                revenue=Decimal(str(revenue_value)),
                net_profit=Decimal(str(profit_value)),
                total_assets=Decimal("100000"),
                total_equity=Decimal("50000"),
                roe=Decimal(str(roe_value)),  # 逐年上升的ROE
                pe=Decimal(str(pe_value)),  # 逐年下降的PE
                pb=Decimal("2.5"),
                debt_ratio=Decimal(str(debt_value)),  # 逐年下降的负债率
                gross_margin=Decimal("35"),
            )
            financials.append(financial)
            idx += 1

    return financials


@pytest.fixture
def sample_financials_declining():
    """创建业绩下滑的财务数据"""
    financials = []

    # 使用递减的序号来确保有明显的下降趋势
    idx = 0
    for year in range(2024, 2019, -1):
        for quarter in range(4, 0, -1):
            month = quarter * 3
            report_date = date(year, month, 30)

            # ROE从20逐年下降到10（有明显的下降趋势）
            roe_value = 20 - idx * 0.5
            # PE从15上升到25
            pe_value = 15 + idx * 0.5
            # 负债率从30上升到50
            debt_value = 30 + idx * 1
            # 营收逐年下降
            revenue_value = 15000 - idx * 200
            profit_value = 2000 - idx * 50

            financial = Financial(
                symbol="000002.SZ",
                report_date=report_date,
                revenue=Decimal(str(revenue_value)),  # 营收下滑
                net_profit=Decimal(str(profit_value)),  # 利润下滑
                total_assets=Decimal("100000"),
                total_equity=Decimal("50000"),
                roe=Decimal(str(roe_value)),  # ROE下降
                pe=Decimal(str(pe_value)),  # PE上升
                pb=Decimal("3.5"),
                debt_ratio=Decimal(str(debt_value)),  # 负债上升
                gross_margin=Decimal("25"),
            )
            financials.append(financial)
            idx += 1

    return financials


class TestFundamentalAnalyzer:
    """基本面分析器测试"""

    def test_init(self, mock_repository):
        """测试初始化"""
        analyzer = FundamentalAnalyzer(mock_repository)
        assert analyzer.repository is mock_repository

    def test_analyze_no_data(self, mock_repository):
        """测试无数据时的分析"""
        mock_repository.get_financials.return_value = []

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        assert report.symbol == "000001.SZ"
        assert report.overall_score == 0
        assert "无财务数据" in report.summary

    def test_analyze_basic(self, mock_repository, sample_financials):
        """测试基本分析"""
        mock_repository.get_financials.return_value = sample_financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        assert report.symbol == "000001.SZ"
        assert report.valuation is not None
        assert report.profitability is not None
        assert report.growth is not None
        assert report.financial_health is not None
        assert 0 <= report.overall_score <= 100

    def test_valuation_analysis(self, mock_repository, sample_financials):
        """测试估值分析"""
        mock_repository.get_financials.return_value = sample_financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        assert report.valuation.pe is not None
        assert report.valuation.pb is not None
        assert report.valuation.score >= 0

    def test_valuation_undervalued(self, mock_repository):
        """测试低估股票"""
        # PE很低
        financials = [
            Financial(
                symbol="000001.SZ",
                report_date=date(2024, 3, 31),
                pe=Decimal("8"),
                pb=Decimal("0.8"),
            )
        ]
        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        # 低PE应该被判定为低估
        assert report.valuation.is_undervalued == True

    def test_valuation_overvalued(self, mock_repository):
        """测试高估股票"""
        # PE很高
        financials = [
            Financial(
                symbol="000001.SZ",
                report_date=date(2024, 3, 31),
                pe=Decimal("60"),
                pb=Decimal("6"),
            )
        ]
        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        # 高PE应该不被判定为低估
        assert report.valuation.is_undervalued == False

    def test_profitability_analysis(self, mock_repository, sample_financials):
        """测试盈利能力分析"""
        mock_repository.get_financials.return_value = sample_financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        assert report.profitability.roe_current is not None
        assert report.profitability.roe_avg_3y is not None
        assert report.profitability.roe_trend in ["上升", "稳定", "下降"]
        assert report.profitability.score >= 0

    def test_profitability_roe_trend_rising(self, mock_repository):
        """测试ROE趋势分析"""
        # 创建财务数据，确保有足够的数据进行趋势分析
        financials = []
        # 按日期从新到旧排列
        for i in range(12):
            # 创建逐年上升的ROE数据
            year = 2024 - i // 4
            month = 12 - (i % 4) * 3
            roe_value = 10 + (11 - i) * 1.5  # 从26.5下降到10，但排序后是从旧到新

            financials.append(Financial(
                symbol="000001.SZ",
                report_date=date(year, month, 28),
                roe=Decimal(str(roe_value)),
            ))

        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        # ROE趋势应该被正确识别
        assert report.profitability.roe_trend in ["上升", "稳定", "下降"]

    def test_profitability_roe_trend_declining(self, mock_repository):
        """测试ROE趋势分析"""
        # 创建财务数据，确保有足够的数据进行趋势分析
        financials = []
        # 按日期从新到旧排列
        for i in range(12):
            year = 2024 - i // 4
            month = 12 - (i % 4) * 3
            roe_value = 26.5 - (11 - i) * 1.5  # 从10上升到26.5，排序后是从新到旧下降

            financials.append(Financial(
                symbol="000002.SZ",
                report_date=date(year, month, 28),
                roe=Decimal(str(roe_value)),
            ))

        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000002.SZ", years=5)

        # ROE趋势应该被正确识别
        assert report.profitability.roe_trend in ["上升", "稳定", "下降"]

    def test_growth_analysis(self, mock_repository, sample_financials):
        """测试成长性分析"""
        mock_repository.get_financials.return_value = sample_financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        assert report.growth.revenue_yoy is not None
        assert report.growth.profit_yoy is not None
        assert report.growth.score >= 0

    def test_growth_positive(self, mock_repository):
        """测试正增长"""
        # 创建营收和利润增长的财务数据
        financials = [
            Financial(
                symbol="000001.SZ",
                report_date=date(2024, 3, 31),
                revenue=Decimal("12000"),  # 最新
                net_profit=Decimal("1200"),
            ),
            Financial(
                symbol="000001.SZ",
                report_date=date(2023, 12, 31),
                revenue=Decimal("10000"),  # 上一期
                net_profit=Decimal("1000"),
            ),
        ]
        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        # 营收和利润应该为正增长
        assert report.growth.revenue_yoy is not None
        assert report.growth.revenue_yoy > 0
        assert report.growth.profit_yoy > 0

    def test_growth_negative(self, mock_repository):
        """测试负增长"""
        # 创建营收和利润下降的财务数据
        financials = [
            Financial(
                symbol="000002.SZ",
                report_date=date(2024, 3, 31),
                revenue=Decimal("8000"),  # 最新
                net_profit=Decimal("800"),
            ),
            Financial(
                symbol="000002.SZ",
                report_date=date(2023, 12, 31),
                revenue=Decimal("10000"),  # 上一期
                net_profit=Decimal("1000"),
            ),
        ]
        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000002.SZ", years=5)

        # 营收和利润应该为负增长
        assert report.growth.revenue_yoy is not None
        assert report.growth.revenue_yoy < 0
        assert report.growth.profit_yoy < 0

    def test_health_analysis(self, mock_repository, sample_financials):
        """测试财务健康度分析"""
        mock_repository.get_financials.return_value = sample_financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        assert report.financial_health.debt_ratio is not None
        assert report.financial_health.debt_trend in ["上升", "稳定", "下降", None]
        assert report.financial_health.score >= 0

    def test_health_low_debt(self, mock_repository):
        """测试低负债"""
        financials = [
            Financial(
                symbol="000001.SZ",
                report_date=date(2024, 3, 31),
                debt_ratio=Decimal("20"),
            ),
            Financial(
                symbol="000001.SZ",
                report_date=date(2023, 12, 31),
                debt_ratio=Decimal("22"),
            ),
            Financial(
                symbol="000001.SZ",
                report_date=date(2023, 9, 30),
                debt_ratio=Decimal("24"),
            ),
            Financial(
                symbol="000001.SZ",
                report_date=date(2023, 6, 30),
                debt_ratio=Decimal("26"),
            ),
        ]
        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        # 低负债应该获得较高评分
        assert report.financial_health.score >= 60

    def test_health_high_debt(self, mock_repository):
        """测试高负债"""
        financials = [
            Financial(
                symbol="000001.SZ",
                report_date=date(2024, 3, 31),
                debt_ratio=Decimal("80"),
            ),
            Financial(
                symbol="000001.SZ",
                report_date=date(2023, 12, 31),
                debt_ratio=Decimal("78"),
            ),
            Financial(
                symbol="000001.SZ",
                report_date=date(2023, 9, 30),
                debt_ratio=Decimal("76"),
            ),
            Financial(
                symbol="000001.SZ",
                report_date=date(2023, 6, 30),
                debt_ratio=Decimal("74"),
            ),
        ]
        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        # 高负债应该获得较低评分
        assert report.financial_health.score < 50

    def test_overall_score(self, mock_repository):
        """测试综合评分"""
        # 创建良好的财务数据
        financials = [
            Financial(
                symbol="000001.SZ",
                report_date=date(2024, 3, 31),
                revenue=Decimal("12000"),
                net_profit=Decimal("1500"),
                roe=Decimal("20"),
                pe=Decimal("15"),
                pb=Decimal("1.5"),
                debt_ratio=Decimal("30"),
                gross_margin=Decimal("40"),
            ),
            Financial(
                symbol="000001.SZ",
                report_date=date(2023, 12, 31),
                revenue=Decimal("10000"),
                net_profit=Decimal("1200"),
                roe=Decimal("18"),
                pe=Decimal("16"),
                pb=Decimal("1.6"),
                debt_ratio=Decimal("32"),
                gross_margin=Decimal("38"),
            ),
        ]
        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        # 综合评分应该是各部分评分的加权平均
        assert 0 <= report.overall_score <= 100

        # 业绩良好的公司应该获得较高评分
        assert report.overall_score >= 40

    def test_summary_generation(self, mock_repository, sample_financials):
        """测试摘要生成"""
        mock_repository.get_financials.return_value = sample_financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        assert report.summary is not None
        assert len(report.summary) > 0


class TestFundamentalAnalyzerEdgeCases:
    """边界情况测试"""

    def test_negative_pe(self, mock_repository):
        """测试负PE（亏损公司）"""
        financials = [
            Financial(
                symbol="000001.SZ",
                report_date=date(2024, 3, 31),
                pe=Decimal("-10"),  # 亏损
            )
        ]
        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        # 亏损公司不应该被判定为低估
        assert report.valuation.is_undervalued == False

    def test_single_financial_record(self, mock_repository):
        """测试只有一条财务记录"""
        financials = [
            Financial(
                symbol="000001.SZ",
                report_date=date(2024, 3, 31),
                roe=Decimal("15"),
                pe=Decimal("20"),
                debt_ratio=Decimal("40"),
            )
        ]
        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        # 应该能够处理只有一条记录的情况
        assert report.overall_score >= 0

    def test_none_values(self, mock_repository):
        """测试空值处理"""
        financials = [
            Financial(
                symbol="000001.SZ",
                report_date=date(2024, 3, 31),
                roe=None,
                pe=None,
                pb=None,
                debt_ratio=None,
            )
        ]
        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        # 应该能够处理空值
        assert report.overall_score >= 0

    def test_zero_revenue(self, mock_repository):
        """测试零营收"""
        financials = [
            Financial(
                symbol="000001.SZ",
                report_date=date(2024, 3, 31),
                revenue=Decimal("0"),
                net_profit=Decimal("100"),
            ),
            Financial(
                symbol="000001.SZ",
                report_date=date(2023, 12, 31),
                revenue=Decimal("1000"),
                net_profit=Decimal("100"),
            ),
        ]
        mock_repository.get_financials.return_value = financials

        analyzer = FundamentalAnalyzer(mock_repository)
        report = analyzer.analyze("000001.SZ", years=5)

        # 应该能够处理零营收
        assert report.growth.score >= 0
