"""
数据源基类
定义所有数据源（Tushare、YFinance、Futu）的统一接口
"""

from abc import ABC, abstractmethod
from datetime import date

from src.models.schemas import DailyQuote, Financial, StockInfo


class BaseProvider(ABC):
    """数据源基类"""

    @abstractmethod
    def get_daily_quotes(self, symbol: str, start: date, end: date) -> list[DailyQuote]:
        """获取日线行情

        Args:
            symbol: 股票代码
            start: 开始日期
            end: 结束日期

        Returns:
            日线行情列表
        """
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> StockInfo | None:
        """获取股票基础信息

        Args:
            symbol: 股票代码

        Returns:
            股票基础信息，不存在则返回None
        """
        pass

    @abstractmethod
    def get_financials(self, symbol: str, years: int = 5) -> list[Financial]:
        """获取财务数据

        Args:
            symbol: 股票代码
            years: 获取最近几年的数据

        Returns:
            财务数据列表
        """
        pass

    @abstractmethod
    def search_stocks(self, keyword: str) -> list[StockInfo]:
        """搜索股票

        Args:
            keyword: 搜索关键词（股票代码或名称）

        Returns:
            匹配的股票信息列表
        """
        pass
