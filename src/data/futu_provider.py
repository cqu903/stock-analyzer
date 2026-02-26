"""
富途数据源（港股）
提供港股市场股票行情和财务数据
"""

from datetime import date
from decimal import Decimal

from loguru import logger

from src.data.base import BaseProvider
from src.models.schemas import DailyQuote, Financial, Market, StockInfo


class FutuProvider(BaseProvider):
    """富途数据源（港股）"""

    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        self.host = host
        self.port = port

    def _get_quote_ctx(self):
        """获取行情上下文"""
        from futu import OpenQuoteContext
        return OpenQuoteContext(self.host, self.port)

    def _parse_symbol(self, symbol: str) -> tuple[str, Market]:
        """解析股票代码"""
        if symbol.endswith(".HK"):
            code = symbol[:-3]
            return f"HK.{code}", Market.HK_STOCK
        if symbol.startswith("0") and len(symbol) == 5:
            return f"HK.{symbol}", Market.HK_STOCK
        return symbol, Market.HK_STOCK

    def get_daily_quotes(self, symbol: str, start: date, end: date) -> list[DailyQuote]:
        """获取日线行情"""
        futu_symbol, _ = self._parse_symbol(symbol)

        with self._get_quote_ctx() as ctx:
            from futu import KLType
            ret, df = ctx.request_history_kline(
                futu_symbol,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                ktype=KLType.K_DAY,
            )
            if ret != 0:
                logger.error(f"获取行情失败: {df}")
                return []

        quotes = []
        for _, row in df.iterrows():
            quotes.append(DailyQuote(
                symbol=symbol,
                trade_date=row["time_key"].date() if hasattr(row["time_key"], "date") else date.fromisoformat(row["time_key"]),
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=int(row["volume"]),
                amount=Decimal(str(row["turnover"])),
            ))
        return quotes

    def get_stock_info(self, symbol: str) -> StockInfo | None:
        """获取股票基础信息"""
        futu_symbol, market = self._parse_symbol(symbol)

        with self._get_quote_ctx() as ctx:
            ret, df = ctx.get_stock_basicinfo(market="HK", code=futu_symbol)
            if ret != 0 or df.empty:
                return None

        row = df.iloc[0]
        return StockInfo(
            symbol=symbol,
            name=row["name"],
            market=market,
        )

    def get_financials(self, symbol: str, years: int = 5) -> list[Financial]:
        """获取财务数据 - 富途API有限支持"""
        # 港股财务数据需要使用其他接口或数据源
        return []

    def search_stocks(self, keyword: str) -> list[StockInfo]:
        """搜索股票"""
        with self._get_quote_ctx() as ctx:
            ret, df = ctx.get_stock_filter(market="HK", filter_list=[])
            if ret != 0:
                return []

        results = []
        for _, row in df.iterrows():
            if keyword in row.get("name", ""):
                results.append(StockInfo(
                    symbol=row["code"],
                    name=row["name"],
                    market=Market.HK_STOCK,
                ))
        return results[:20]
