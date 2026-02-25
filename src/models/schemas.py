"""
Pydantic数据模型定义
包含股票基础信息、行情数据、财务数据、分析报告等数据结构
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


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
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")
    amount: Optional[float] = Field(None, description="成交额")
    turnover_rate: Optional[float] = Field(None, description="换手率")


class Financial(BaseModel):
    """财务数据"""
    symbol: str = Field(..., description="股票代码")
    report_date: date = Field(..., description="报告期")
    revenue: Optional[float] = Field(None, description="营业收入")
    net_profit: Optional[float] = Field(None, description="净利润")
    total_assets: Optional[float] = Field(None, description="总资产")
    total_equity: Optional[float] = Field(None, description="股东权益")
    roe: Optional[float] = Field(None, description="净资产收益率")
    pe: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    debt_ratio: Optional[float] = Field(None, description="资产负债率")
    gross_margin: Optional[float] = Field(None, description="毛利率")


class WatchlistItem(BaseModel):
    """自选股项目"""
    symbol: str = Field(..., description="股票代码")
    added_at: datetime = Field(default_factory=datetime.now, description="添加时间")
    notes: Optional[str] = Field(None, description="用户备注")
    alert_price_high: Optional[float] = Field(None, description="价格上限预警")
    alert_price_low: Optional[float] = Field(None, description="价格下限预警")


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
    pe: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    pe_industry_avg: Optional[float] = Field(None, description="行业平均市盈率")
    pb_industry_avg: Optional[float] = Field(None, description="行业平均市净率")
    valuation_level: str = Field(..., description="估值水平：低估/合理/高估")
    score: int = Field(..., ge=0, le=100, description="估值评分")


class ProfitabilityResult(BaseModel):
    """盈利能力分析结果"""
    roe: Optional[float] = Field(None, description="净资产收益率")
    gross_margin: Optional[float] = Field(None, description="毛利率")
    net_margin: Optional[float] = Field(None, description="净利率")
    roe_trend: str = Field(..., description="ROE趋势：上升/稳定/下降")
    score: int = Field(..., ge=0, le=100, description="盈利能力评分")


class GrowthResult(BaseModel):
    """成长性分析结果"""
    revenue_growth: Optional[float] = Field(None, description="营收同比增长率")
    profit_growth: Optional[float] = Field(None, description="利润同比增长率")
    cagr_3y: Optional[float] = Field(None, description="3年复合增长率")
    growth_level: str = Field(..., description="成长水平：高增长/稳定/下滑")
    score: int = Field(..., ge=0, le=100, description="成长性评分")


class HealthResult(BaseModel):
    """财务健康度分析结果"""
    debt_ratio: Optional[float] = Field(None, description="资产负债率")
    current_ratio: Optional[float] = Field(None, description="流动比率")
    quick_ratio: Optional[float] = Field(None, description="速动比率")
    health_level: str = Field(..., description="健康度：健康/一般/风险")
    score: int = Field(..., ge=0, le=100, description="健康度评分")


class FundamentalReport(BaseModel):
    """基本面分析报告"""
    symbol: str = Field(..., description="股票代码")
    analysis_date: date = Field(default_factory=date.today, description="分析日期")
    valuation: Optional[ValuationResult] = Field(None, description="估值分析")
    profitability: Optional[ProfitabilityResult] = Field(None, description="盈利能力分析")
    growth: Optional[GrowthResult] = Field(None, description="成长性分析")
    health: Optional[HealthResult] = Field(None, description="财务健康度分析")
    overall_score: int = Field(..., ge=0, le=100, description="综合评分")
    summary: Optional[str] = Field(None, description="分析摘要")


# ============== 技术面分析模型 ==============

class MACDResult(BaseModel):
    """MACD指标结果"""
    dif: float = Field(..., description="DIF值")
    dea: float = Field(..., description="DEA值")
    macd: float = Field(..., description="MACD柱值")
    signal: str = Field(..., description="信号：金叉/死叉/多头/空头/震荡")


class KDJResult(BaseModel):
    """KDJ指标结果"""
    k: float = Field(..., description="K值")
    d: float = Field(..., description="D值")
    j: float = Field(..., description="J值")
    signal: str = Field(..., description="信号：超买/超卖/正常")


class RSIResult(BaseModel):
    """RSI指标结果"""
    rsi_6: Optional[float] = Field(None, description="6日RSI")
    rsi_12: Optional[float] = Field(None, description="12日RSI")
    rsi_24: Optional[float] = Field(None, description="24日RSI")
    signal: str = Field(..., description="信号：超买/超卖/正常")


class BollingerBandsResult(BaseModel):
    """布林带指标结果"""
    upper: float = Field(..., description="上轨")
    middle: float = Field(..., description="中轨")
    lower: float = Field(..., description="下轨")
    position: str = Field(..., description="位置：上轨上方/上轨附近/中轨附近/下轨附近/下轨下方")


class Indicators(BaseModel):
    """技术指标集合"""
    macd: Optional[MACDResult] = Field(None, description="MACD指标")
    kdj: Optional[KDJResult] = Field(None, description="KDJ指标")
    rsi: Optional[RSIResult] = Field(None, description="RSI指标")
    bollinger_bands: Optional[BollingerBandsResult] = Field(None, description="布林带指标")
    ma5: Optional[float] = Field(None, description="5日均线")
    ma10: Optional[float] = Field(None, description="10日均线")
    ma20: Optional[float] = Field(None, description="20日均线")
    ma60: Optional[float] = Field(None, description="60日均线")


class TrendResult(BaseModel):
    """趋势分析结果"""
    short_term: str = Field(..., description="短期趋势：上涨/下跌/震荡")
    medium_term: str = Field(..., description="中期趋势：上涨/下跌/震荡")
    long_term: str = Field(..., description="长期趋势：上涨/下跌/震荡")
    trend_strength: int = Field(..., ge=0, le=100, description="趋势强度")


class SupportResistance(BaseModel):
    """支撑压力位"""
    support_levels: list[float] = Field(default_factory=list, description="支撑位列表")
    resistance_levels: list[float] = Field(default_factory=list, description="压力位列表")
    current_price: float = Field(..., description="当前价格")
    nearest_support: Optional[float] = Field(None, description="最近支撑位")
    nearest_resistance: Optional[float] = Field(None, description="最近压力位")


class TechnicalReport(BaseModel):
    """技术面分析报告"""
    symbol: str = Field(..., description="股票代码")
    analysis_date: date = Field(default_factory=date.today, description="分析日期")
    trend: Optional[TrendResult] = Field(None, description="趋势分析")
    indicators: Optional[Indicators] = Field(None, description="技术指标")
    support_resistance: Optional[SupportResistance] = Field(None, description="支撑压力位")
    signal_summary: str = Field(..., description="信号汇总：买入/卖出/观望")
    score: int = Field(..., ge=0, le=100, description="技术面评分")


# ============== AI分析模型 ==============

class AIAnalysis(BaseModel):
    """AI分析报告"""
    symbol: str = Field(..., description="股票代码")
    analysis_date: datetime = Field(default_factory=datetime.now, description="分析时间")
    fundamental_summary: Optional[str] = Field(None, description="基本面分析摘要")
    technical_summary: Optional[str] = Field(None, description="技术面分析摘要")
    risk_assessment: Optional[str] = Field(None, description="风险评估")
    investment_advice: Optional[str] = Field(None, description="投资建议")
    key_points: list[str] = Field(default_factory=list, description="关键要点")
    confidence: int = Field(..., ge=0, le=100, description="置信度")
