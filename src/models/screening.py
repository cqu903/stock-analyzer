"""量化选股相关数据模型"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class Strategy(BaseModel):
    """策略模板模型"""

    id: str = Field(..., description="策略ID")
    name: str = Field(..., description="策略名称")
    description: str = Field(..., description="策略描述")
    category: str = Field(..., description="策略分类")
    params: dict[str, Any] = Field(default_factory=dict, description="可调参数")


class ScreenResult(BaseModel):
    """筛选结果模型"""

    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    score: float = Field(..., ge=0, le=100, description="匹配分数")
    match_details: dict[str, Any] = Field(default_factory=dict, description="各项指标")
    current_price: Decimal | None = Field(None, description="当前价格")
