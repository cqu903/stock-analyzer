"""组合管理相关数据模型"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, computed_field


class AccountType(str, Enum):
    """账户类型枚举"""
    SECURITIES = "证券账户"
    SIMULATION = "模拟账户"


class TradeType(str, Enum):
    """交易类型枚举"""
    BUY = "买入"
    SELL = "卖出"


class Account(BaseModel):
    """账户模型"""
    id: int | None = Field(None, description="账户ID")
    name: str = Field(..., description="账户名称")
    account_type: AccountType = Field(default=AccountType.SECURITIES, description="账户类型")
    initial_capital: Decimal = Field(..., ge=0, description="初始资金")
    current_cash: Decimal = Field(..., ge=0, description="当前现金")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    @property
    def total_assets(self) -> Decimal:
        """总资产 = 现金（不含持仓，持仓单独计算）"""
        return self.current_cash


class Transaction(BaseModel):
    """交易记录模型"""
    id: int | None = Field(None, description="交易ID")
    account_id: int = Field(..., description="所属账户ID")
    symbol: str = Field(..., description="股票代码")
    trade_type: TradeType = Field(..., description="交易类型")
    shares: int = Field(..., gt=0, description="成交数量")
    price: Decimal = Field(..., gt=0, description="成交价格")
    amount: Decimal = Field(..., ge=0, description="成交金额")
    fee: Decimal = Field(default=Decimal("0"), ge=0, description="手续费")
    trade_date: date = Field(..., description="交易日期")
    notes: str | None = Field(None, description="备注")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class Position(BaseModel):
    """持仓记录模型（计算得出）"""
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    shares: int = Field(..., ge=0, description="持仓数量")
    avg_cost: Decimal = Field(..., ge=0, description="平均成本价")
    current_price: Decimal = Field(..., ge=0, description="当前价格")
    market_value: Decimal = Field(..., ge=0, description="市值")
    cost_value: Decimal = Field(..., ge=0, description="成本值")
    unrealized_pnl: Decimal = Field(..., description="未实现盈亏")
    unrealized_pnl_pct: Decimal = Field(..., description="未实现盈亏百分比")


class AccountSummary(BaseModel):
    """账户汇总"""
    total_assets: Decimal = Field(..., ge=0, description="总资产")
    cash: Decimal = Field(..., ge=0, description="现金")
    positions_value: Decimal = Field(..., ge=0, description="持仓市值")
    total_pnl: Decimal = Field(..., description="总盈亏")
    total_pnl_pct: Decimal = Field(..., description="总盈亏百分比")
    total_cost: Decimal = Field(default=Decimal("0"), ge=0, description="总成本")
