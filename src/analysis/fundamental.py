"""
基本面分析器
提供估值分析、盈利能力分析、成长性分析、财务健康度分析等功能
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from loguru import logger

from src.data.repository import Repository
from src.models.schemas import (
    Financial,
    FundamentalReport,
    GrowthResult,
    HealthResult,
    ProfitabilityResult,
    ValuationResult,
)


class FundamentalAnalyzer:
    """基本面分析器

    对股票进行基本面分析，包括估值、盈利能力、成长性、财务健康度等方面
    """

    def __init__(self, repository: Repository):
        """初始化基本面分析器

        Args:
            repository: 数据访问层实例
        """
        self.repository = repository
        logger.info("FundamentalAnalyzer initialized")

    def analyze(self, symbol: str, years: int = 5) -> FundamentalReport:
        """执行基本面分析

        Args:
            symbol: 股票代码
            years: 分析年数，默认5年

        Returns:
            FundamentalReport: 基本面分析报告
        """
        logger.info(f"Starting fundamental analysis for {symbol}, years={years}")

        # 获取财务数据
        financials = self.repository.get_financials(symbol, years)
        if not financials:
            logger.warning(f"No financial data found for {symbol}")
            return FundamentalReport(
                symbol=symbol,
                analysis_date=date.today(),
                overall_score=0,
                summary="无财务数据，无法进行基本面分析",
            )

        # 按报告日期排序（最新的在前）
        financials = sorted(financials, key=lambda x: x.report_date, reverse=True)

        # 估值分析
        valuation = self._analyze_valuation(financials)

        # 盈利能力分析
        profitability = self._analyze_profitability(financials)

        # 成长性分析
        growth = self._analyze_growth(financials)

        # 财务健康度分析
        financial_health = self._analyze_health(financials)

        # 计算综合评分
        overall_score = self._calculate_overall_score(
            valuation, profitability, growth, financial_health
        )

        # 生成摘要
        summary = self._generate_summary(
            valuation, profitability, growth, financial_health, overall_score
        )

        report = FundamentalReport(
            symbol=symbol,
            analysis_date=date.today(),
            valuation=valuation,
            profitability=profitability,
            growth=growth,
            financial_health=financial_health,
            overall_score=overall_score,
            summary=summary,
        )

        logger.info(f"Fundamental analysis completed for {symbol}, score={overall_score}")
        return report

    def _analyze_valuation(self, financials: list[Financial]) -> ValuationResult:
        """估值分析

        Args:
            financials: 财务数据列表

        Returns:
            ValuationResult: 估值分析结果
        """
        latest = financials[0] if financials else None

        if not latest:
            return ValuationResult(score=50)

        pe = latest.pe
        pb = latest.pb

        # 评分计算
        score = 50

        # PE估值分析
        is_undervalued = None
        if pe is not None:
            if pe > 0:
                if pe < 15:
                    score += 20  # 低PE，可能低估
                    is_undervalued = True
                elif pe < 25:
                    score += 10  # 合理PE
                    is_undervalued = False
                elif pe < 40:
                    score += 0  # 略高PE
                    is_undervalued = False
                else:
                    score -= 10  # 高PE，可能高估
                    is_undervalued = False
            else:
                # PE为负，亏损公司
                score -= 20
                is_undervalued = False

        # PB估值分析
        if pb is not None:
            if pb > 0:
                if pb < 1:
                    score += 15  # 低于净资产
                elif pb < 2:
                    score += 5  # 合理PB
                elif pb > 5:
                    score -= 10  # 高PB

        return ValuationResult(
            pe=pe,
            pb=pb,
            is_undervalued=is_undervalued,
            score=max(0, min(100, score)),
        )

    def _analyze_profitability(self, financials: list[Financial]) -> ProfitabilityResult:
        """盈利能力分析

        Args:
            financials: 财务数据列表

        Returns:
            ProfitabilityResult: 盈利能力分析结果
        """
        if not financials:
            return ProfitabilityResult(roe_trend="未知", score=50)

        latest = financials[0]
        roe_current = latest.roe
        gross_margin = latest.gross_margin

        # 计算3年平均ROE
        roe_values = [float(f.roe) for f in financials[:12] if f.roe is not None]  # 最近12个季度（约3年）
        roe_avg_3y = None
        if roe_values:
            roe_avg_3y = Decimal(str(sum(roe_values) / len(roe_values)))

        # 判断ROE趋势
        roe_trend = "稳定"
        if len(roe_values) >= 3:
            recent_avg = sum(roe_values[:3]) / 3
            older_avg = sum(roe_values[3:6]) / len(roe_values[3:6]) if len(roe_values) >= 6 else recent_avg

            if recent_avg > older_avg * 1.1:
                roe_trend = "上升"
            elif recent_avg < older_avg * 0.9:
                roe_trend = "下降"

        # 评分计算
        score = 50

        # ROE评分
        if roe_current is not None:
            if roe_current > 20:
                score += 25
            elif roe_current > 15:
                score += 15
            elif roe_current > 10:
                score += 5
            elif roe_current > 5:
                score += 0
            else:
                score -= 10

        # ROE趋势评分
        if roe_trend == "上升":
            score += 10
        elif roe_trend == "下降":
            score -= 10

        # 毛利率评分
        if gross_margin is not None:
            if gross_margin > 40:
                score += 10
            elif gross_margin > 20:
                score += 5
            elif gross_margin < 10:
                score -= 5

        return ProfitabilityResult(
            roe_current=roe_current,
            roe_avg_3y=roe_avg_3y,
            gross_margin=gross_margin,
            roe_trend=roe_trend,
            score=max(0, min(100, score)),
        )

    def _analyze_growth(self, financials: list[Financial]) -> GrowthResult:
        """成长性分析

        Args:
            financials: 财务数据列表

        Returns:
            GrowthResult: 成长性分析结果
        """
        if len(financials) < 2:
            return GrowthResult(score=50)

        latest = financials[0]
        previous = financials[1] if len(financials) > 1 else None

        # 计算同比增长率
        revenue_yoy = None
        profit_yoy = None

        if latest.revenue and previous and previous.revenue and previous.revenue != 0:
            revenue_yoy = (latest.revenue - previous.revenue) / previous.revenue * 100

        if latest.net_profit and previous and previous.net_profit and previous.net_profit != 0:
            profit_yoy = (latest.net_profit - previous.net_profit) / previous.net_profit * 100

        # 计算3年复合增长率（CAGR）
        revenue_cagr_3y = None
        if len(financials) >= 12:  # 至少3年数据（假设每年4个季度）
            # 找到约3年前的数据
            oldest = financials[-1]
            if (
                oldest.revenue
                and latest.revenue
                and oldest.revenue > 0
                and latest.revenue > 0
            ):
                years = (latest.report_date - oldest.report_date).days / 365
                if years > 0:
                    cagr = (float(latest.revenue) / float(oldest.revenue)) ** (1 / years) - 1
                    revenue_cagr_3y = Decimal(str(cagr * 100))

        # 评分计算
        score = 50

        # 营收增长评分
        if revenue_yoy is not None:
            if revenue_yoy > 30:
                score += 20
            elif revenue_yoy > 15:
                score += 10
            elif revenue_yoy > 5:
                score += 5
            elif revenue_yoy < -10:
                score -= 15
            elif revenue_yoy < 0:
                score -= 5

        # 利润增长评分
        if profit_yoy is not None:
            if profit_yoy > 30:
                score += 20
            elif profit_yoy > 15:
                score += 10
            elif profit_yoy > 5:
                score += 5
            elif profit_yoy < -10:
                score -= 15
            elif profit_yoy < 0:
                score -= 5

        # CAGR评分
        if revenue_cagr_3y is not None:
            if revenue_cagr_3y > 20:
                score += 10
            elif revenue_cagr_3y > 10:
                score += 5

        return GrowthResult(
            revenue_yoy=revenue_yoy,
            profit_yoy=profit_yoy,
            revenue_cagr_3y=revenue_cagr_3y,
            score=max(0, min(100, score)),
        )

    def _analyze_health(self, financials: list[Financial]) -> HealthResult:
        """财务健康度分析

        Args:
            financials: 财务数据列表

        Returns:
            HealthResult: 财务健康度分析结果
        """
        if not financials:
            return HealthResult(score=50)

        latest = financials[0]
        debt_ratio = latest.debt_ratio

        # 判断负债率趋势
        debt_trend = "稳定"
        if len(financials) >= 4:
            recent_ratios = [float(f.debt_ratio) for f in financials[:4] if f.debt_ratio is not None]
            if len(recent_ratios) >= 4:
                recent_avg = sum(recent_ratios[:2]) / 2
                older_avg = sum(recent_ratios[2:4]) / 2

                if recent_avg > older_avg * 1.1:
                    debt_trend = "上升"  # 负债增加，不好
                elif recent_avg < older_avg * 0.9:
                    debt_trend = "下降"  # 负债减少，好

        # 评分计算
        score = 50

        # 负债率评分
        if debt_ratio is not None:
            if debt_ratio < 30:
                score += 25  # 低负债
            elif debt_ratio < 50:
                score += 15  # 适中负债
            elif debt_ratio < 70:
                score += 0  # 较高负债
            else:
                score -= 20  # 高负债

        # 负债趋势评分
        if debt_trend == "下降":
            score += 10
        elif debt_trend == "上升":
            score -= 10

        return HealthResult(
            debt_ratio=debt_ratio,
            debt_trend=debt_trend,
            score=max(0, min(100, score)),
        )

    def _calculate_overall_score(
        self,
        valuation: ValuationResult,
        profitability: ProfitabilityResult,
        growth: GrowthResult,
        health: HealthResult,
    ) -> int:
        """计算综合评分

        Args:
            valuation: 估值分析结果
            profitability: 盈利能力分析结果
            growth: 成长性分析结果
            health: 财务健康度分析结果

        Returns:
            int: 综合评分（0-100）
        """
        # 权重分配
        weights = {
            "valuation": 0.25,
            "profitability": 0.30,
            "growth": 0.25,
            "health": 0.20,
        }

        weighted_score = (
            valuation.score * weights["valuation"]
            + profitability.score * weights["profitability"]
            + growth.score * weights["growth"]
            + health.score * weights["health"]
        )

        return int(round(weighted_score))

    def _generate_summary(
        self,
        valuation: ValuationResult,
        profitability: ProfitabilityResult,
        growth: GrowthResult,
        health: HealthResult,
        overall_score: int,
    ) -> str:
        """生成分析摘要

        Args:
            valuation: 估值分析结果
            profitability: 盈利能力分析结果
            growth: 成长性分析结果
            health: 财务健康度分析结果
            overall_score: 综合评分

        Returns:
            str: 分析摘要
        """
        parts = []

        # 总体评价
        if overall_score >= 80:
            parts.append("基本面优秀")
        elif overall_score >= 60:
            parts.append("基本面良好")
        elif overall_score >= 40:
            parts.append("基本面一般")
        else:
            parts.append("基本面较弱")

        # 估值评价
        if valuation.is_undervalued:
            parts.append("估值偏低")
        elif valuation.pe and valuation.pe > 40:
            parts.append("估值偏高")

        # 盈利能力评价
        if profitability.roe_current and profitability.roe_current > 15:
            parts.append(f"ROE达{profitability.roe_current:.1f}%")
        if profitability.roe_trend == "上升":
            parts.append("盈利能力提升中")

        # 成长性评价
        if growth.revenue_yoy and growth.revenue_yoy > 20:
            parts.append(f"营收增长{growth.revenue_yoy:.1f}%")
        if growth.profit_yoy and growth.profit_yoy > 20:
            parts.append(f"利润增长{growth.profit_yoy:.1f}%")

        # 财务健康评价
        if health.debt_ratio and health.debt_ratio < 40:
            parts.append("财务稳健")
        elif health.debt_ratio and health.debt_ratio > 70:
            parts.append("负债较高需关注")

        return "，".join(parts) if parts else "暂无足够数据进行分析"
