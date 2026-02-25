"""
Pydantic数据模型定义
包含股票基础信息、行情数据、财务数据、分析报告等数据结构
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

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
    industry: Optional[str] = Field(None, description="所属行业")
    list_date: Optional[date] = Field(None, description="上市日期")


class DailyQuote(BaseModel):
    """日线行情数据"""
    symbol: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    open: Decimal = Field(..., description="开盘价")
    high: Decimal = Field(..., description="最高价")
    low: Decimal = Field(..., description="最低价")
    close: Decimal = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")
    pre_close: Optional[Decimal] = Field(None, description="前收盘价")
    amount: Optional[Decimal] = Field(None, description="成交额")
    turnover_rate: Optional[Decimal] = Field(None, description="换手率")

    @computed_field
    @property
    def change_pct(self) -> Optional[Decimal]:
        """涨跌幅百分比"""
        if self.pre_close and self.pre_close != 0:
            return (self.close - self.pre_close) / self.pre_close * 100
        return None


class Financial(BaseModel):
    """财务数据"""
    symbol: str = Field(..., description="股票代码")
    report_date: date = Field(..., description="报告期")
    revenue: Optional[Decimal] = Field(None, description="营业收入")
    net_profit: Optional[Decimal] = Field(None, description="净利润")
    total_assets: Optional[Decimal] = Field(None, description="总资产")
    total_equity: Optional[Decimal] = Field(None, description="股东权益")
    roe: Optional[Decimal] = Field(None, description="净资产收益率")
    pe: Optional[Decimal] = Field(None, description="市盈率")
    pb: Optional[Decimal] = Field(None, description="市净率")
    debt_ratio: Optional[Decimal] = Field(None, description="资产负债率")
    gross_margin: Optional[Decimal] = Field(None, description="毛利率")


class WatchlistItem(BaseModel):
    """自选股项目"""
    symbol: str = Field(..., description="股票代码")
    added_at: datetime = Field(default_factory=datetime.now, description="添加时间")
    notes: Optional[str] = Field(None, description="用户备注")
    alert_price_high: Optional[Decimal] = Field(None, description="价格上限预警")
    alert_price_low: Optional[Decimal] = Field(None, description="价格下限预警")


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
    id: Optional[int] = Field(None, description="预警ID")
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
    pe: Optional[Decimal] = Field(None, description="市盈率")
    pb: Optional[Decimal] = Field(None, description="市净率")
    industry_avg_pe: Optional[Decimal] = Field(None, description="行业平均市盈率")
    pe_percentile: Optional[float] = Field(None, description="PE百分位")
    is_undervalued: Optional[bool] = Field(None, description="是否低估")
    score: int = Field(..., ge=0, le=100, description="估值评分")


class ProfitabilityResult(BaseModel):
    """盈利能力分析结果"""
    roe_current: Optional[Decimal] = Field(None, description="当前净资产收益率")
    roe_avg_3y: Optional[Decimal] = Field(None, description="3年平均ROE")
    gross_margin: Optional[Decimal] = Field(None, description="毛利率")
    roe_trend: str = Field(..., description="ROE趋势：上升/稳定/下降")
    score: int = Field(..., ge=0, le=100, description="盈利能力评分")


class GrowthResult(BaseModel):
    """成长性分析结果"""
    revenue_yoy: Optional[Decimal] = Field(None, description="营收同比增长率")
    profit_yoy: Optional[Decimal] = Field(None, description="利润同比增长率")
    revenue_cagr_3y: Optional[Decimal] = Field(None, description="3年营收复合增长率")
    score: int = Field(..., ge=0, le=100, description="成长性评分")


class HealthResult(BaseModel):
    """财务健康度分析结果"""
    debt_ratio: Optional[Decimal] = Field(None, description="资产负债率")
    debt_trend: Optional[str] = Field(None, description="负债率趋势：上升/稳定/下降")
    score: int = Field(..., ge=0, le=100, description="健康度评分")


class FundamentalReport(BaseModel):
    """基本面分析报告"""
    symbol: str = Field(..., description="股票代码")
    analysis_date: date = Field(default_factory=date.today, description="分析日期")
    valuation: Optional[ValuationResult] = Field(None, description="估值分析")
    profitability: Optional[ProfitabilityResult] = Field(None, description="盈利能力分析")
    growth: Optional[GrowthResult] = Field(None, description="成长性分析")
    financial_health: Optional[HealthResult] = Field(None, description="财务健康度分析")
    overall_score: int = Field(..., ge=0, le=100, description="综合评分")
    summary: Optional[str] = Field(None, description="分析摘要")


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
    ma5: Optional[Decimal] = Field(None, description="5日均线")
    ma20: Optional[Decimal] = Field(None, description="20日均线")
    ma60: Optional[Decimal] = Field(None, description="60日均线")
    macd: Optional[MACDResult] = Field(None, description="MACD指标")
    kdj: Optional[KDJResult] = Field(None, description="KDJ指标")
    rsi: Optional[Decimal] = Field(None, description="RSI指标")


class TrendResult(BaseModel):
    """趋势分析结果"""
    direction: str = Field(..., description="趋势方向：上涨/下跌/震荡")
    current_price: Decimal = Field(..., description="当前价格")


class SupportResistance(BaseModel):
    """支撑压力位"""
    resistance_1: Decimal = Field(..., description="第一压力位")
    resistance_2: Optional[Decimal] = Field(None, description="第二压力位")
    support_1: Decimal = Field(..., description="第一支撑位")
    support_2: Optional[Decimal] = Field(None, description="第二支撑位")


class TechnicalReport(BaseModel):
    """技术面分析报告"""
    symbol: str = Field(..., description="股票代码")
    analysis_date: date = Field(default_factory=date.today, description="分析日期")
    trend: Optional[TrendResult] = Field(None, description="趋势分析")
    indicators: Optional[Indicators] = Field(None, description="技术指标")
    support_resistance: Optional[SupportResistance] = Field(None, description="支撑压力位")
    patterns: list[str] = Field(default_factory=list, description="K线形态列表")
    score: int = Field(..., ge=0, le=100, description="技术面评分")


# ============== AI分析模型 ==============

class AIAnalysis(BaseModel):
    """AI分析报告"""
    symbol: str = Field(..., description="股票代码")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    summary: str = Field(..., description="分析摘要")
    recommendation: Optional[str] = Field(None, description="投资建议")
    risks: list[str] = Field(default_factory=list, description="风险列表")
    confidence: int = Field(..., ge=0, le=100, description="置信度")
