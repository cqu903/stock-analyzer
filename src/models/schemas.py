"""
Pydantic数据模型定义
包含股票基础信息、行情数据、财务数据、分析报告等数据结构
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, computed_field


class Market(str, Enum):
    """市场类型枚举"""
    A_STOCK = "A股"
    HK_STOCK = "港股"
    US_STOCK = "美股"


# ============== 基础数据模型 ==============

class StockInfo(BaseModel):
    """股票基础信息"""
    symbol: str = Field(..., description="股票代码，如 000001.SZ, 00700.HK, AAPL.US")
    name: str = Field(..., description="股票名称")
    market: Market = Field(..., description="所属市场")
    industry: str | None = Field(None, description="所属行业")
    list_date: date | None = Field(None, description="上市日期")


class DailyQuote(BaseModel):
    """日线行情数据"""
    symbol: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    open: Decimal = Field(..., description="开盘价")
    high: Decimal = Field(..., description="最高价")
    low: Decimal = Field(..., description="最低价")
    close: Decimal = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")
    pre_close: Decimal | None = Field(None, description="前收盘价")
    amount: Decimal | None = Field(None, description="成交额")
    turnover_rate: Decimal | None = Field(None, description="换手率")

    @computed_field
    @property
    def change_pct(self) -> Decimal | None:
        """涨跌幅百分比"""
        if self.pre_close and self.pre_close != 0:
            return (self.close - self.pre_close) / self.pre_close * 100
        return None


class Financial(BaseModel):
    """财务数据"""
    symbol: str = Field(..., description="股票代码")
    report_date: date = Field(..., description="报告期")
    revenue: Decimal | None = Field(None, description="营业收入")
    net_profit: Decimal | None = Field(None, description="净利润")
    total_assets: Decimal | None = Field(None, description="总资产")
    total_equity: Decimal | None = Field(None, description="股东权益")
    roe: Decimal | None = Field(None, description="净资产收益率")
    pe: Decimal | None = Field(None, description="市盈率")
    pb: Decimal | None = Field(None, description="市净率")
    debt_ratio: Decimal | None = Field(None, description="资产负债率")
    gross_margin: Decimal | None = Field(None, description="毛利率")


class WatchlistItem(BaseModel):
    """自选股项目"""
    symbol: str = Field(..., description="股票代码")
    added_at: datetime = Field(default_factory=datetime.now, description="添加时间")
    notes: str | None = Field(None, description="用户备注")
    alert_price_high: Decimal | None = Field(None, description="价格上限预警")
    alert_price_low: Decimal | None = Field(None, description="价格下限预警")


class AlertType(str, Enum):
    """预警类型枚举"""
    PRICE_BREAK = "价格突破"
    ABNORMAL_VOLATILITY = "异常波动"
    VOLUME_SURGE = "成交量放大"
    MACD_GOLDEN_CROSS = "MACD金叉"
    MACD_DEATH_CROSS = "MACD死叉"
    RSI_OVERBOUGHT = "RSI超买"
    RSI_OVERSOLD = "RSI超卖"
    CUSTOM = "自定义"


class Alert(BaseModel):
    """预警记录"""
    id: int | None = Field(None, description="预警ID")
    symbol: str = Field(..., description="股票代码")
    alert_type: AlertType = Field(..., description="预警类型")
    message: str = Field(..., description="预警消息")
    triggered_at: datetime = Field(default_factory=datetime.now, description="触发时间")
    is_read: bool = Field(False, description="是否已读")


class DataSyncLog(BaseModel):
    """数据同步日志"""
    data_type: str = Field(..., description="数据类型，如 daily_quote, financial")
    market: str = Field(..., description="市场")
    last_sync_date: date = Field(..., description="最后同步日期")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


# ============== 基本面分析模型 ==============

class ValuationResult(BaseModel):
    """估值分析结果"""
    pe: Decimal | None = Field(None, description="市盈率")
    pb: Decimal | None = Field(None, description="市净率")
    industry_avg_pe: Decimal | None = Field(None, description="行业平均市盈率")
    pe_percentile: float | None = Field(None, description="PE百分位")
    is_undervalued: bool | None = Field(None, description="是否低估")
    score: int = Field(..., ge=0, le=100, description="估值评分")


class ProfitabilityResult(BaseModel):
    """盈利能力分析结果"""
    roe_current: Decimal | None = Field(None, description="当前净资产收益率")
    roe_avg_3y: Decimal | None = Field(None, description="3年平均ROE")
    gross_margin: Decimal | None = Field(None, description="毛利率")
    roe_trend: str = Field(..., description="ROE趋势：上升/稳定/下降")
    score: int = Field(..., ge=0, le=100, description="盈利能力评分")


class GrowthResult(BaseModel):
    """成长性分析结果"""
    revenue_yoy: Decimal | None = Field(None, description="营收同比增长率")
    profit_yoy: Decimal | None = Field(None, description="利润同比增长率")
    revenue_cagr_3y: Decimal | None = Field(None, description="3年营收复合增长率")
    score: int = Field(..., ge=0, le=100, description="成长性评分")


class HealthResult(BaseModel):
    """财务健康度分析结果"""
    debt_ratio: Decimal | None = Field(None, description="资产负债率")
    debt_trend: str | None = Field(None, description="负债率趋势：上升/稳定/下降")
    score: int = Field(..., ge=0, le=100, description="健康度评分")


class FundamentalReport(BaseModel):
    """基本面分析报告"""
    symbol: str = Field(..., description="股票代码")
    analysis_date: date = Field(default_factory=date.today, description="分析日期")
    valuation: ValuationResult | None = Field(None, description="估值分析")
    profitability: ProfitabilityResult | None = Field(None, description="盈利能力分析")
    growth: GrowthResult | None = Field(None, description="成长性分析")
    financial_health: HealthResult | None = Field(None, description="财务健康度分析")
    overall_score: int = Field(..., ge=0, le=100, description="综合评分")
    summary: str | None = Field(None, description="分析摘要")


# ============== 技术面分析模型 ==============

class MACDResult(BaseModel):
    """MACD指标结果"""
    dif: Decimal = Field(..., description="DIF值")
    dea: Decimal = Field(..., description="DEA值")
    macd: Decimal = Field(..., description="MACD柱值")

    def is_golden_cross(self) -> bool:
        """判断是否金叉"""
        return self.dif > self.dea and self.macd > 0


class KDJResult(BaseModel):
    """KDJ指标结果"""
    k: Decimal = Field(..., description="K值")
    d: Decimal = Field(..., description="D值")
    j: Decimal = Field(..., description="J值")


class Indicators(BaseModel):
    """技术指标集合"""
    ma5: Decimal | None = Field(None, description="5日均线")
    ma20: Decimal | None = Field(None, description="20日均线")
    ma60: Decimal | None = Field(None, description="60日均线")
    macd: MACDResult | None = Field(None, description="MACD指标")
    kdj: KDJResult | None = Field(None, description="KDJ指标")
    rsi: Decimal | None = Field(None, description="RSI指标")


class TrendResult(BaseModel):
    """趋势分析结果"""
    direction: str = Field(..., description="趋势方向：上涨/下跌/震荡")
    current_price: Decimal = Field(..., description="当前价格")


class SupportResistance(BaseModel):
    """支撑压力位"""
    resistance_1: Decimal = Field(..., description="第一压力位")
    resistance_2: Decimal | None = Field(None, description="第二压力位")
    support_1: Decimal = Field(..., description="第一支撑位")
    support_2: Decimal | None = Field(None, description="第二支撑位")


class TechnicalReport(BaseModel):
    """技术面分析报告"""
    symbol: str = Field(..., description="股票代码")
    analysis_date: date = Field(default_factory=date.today, description="分析日期")
    trend: TrendResult | None = Field(None, description="趋势分析")
    indicators: Indicators | None = Field(None, description="技术指标")
    support_resistance: SupportResistance | None = Field(None, description="支撑压力位")
    patterns: list[str] = Field(default_factory=list, description="K线形态列表")
    score: int = Field(..., ge=0, le=100, description="技术面评分")


# ============== AI分析模型 ==============

class AIAnalysis(BaseModel):
    """AI分析报告"""
    symbol: str = Field(..., description="股票代码")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    summary: str = Field(..., description="分析摘要")
    recommendation: str | None = Field(None, description="投资建议")
    risks: list[str] = Field(default_factory=list, description="风险列表")
    confidence: int = Field(..., ge=0, le=100, description="置信度")
