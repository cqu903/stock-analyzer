from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

import yfinance as yf
from loguru import logger

from src.data.base import BaseProvider
from src.models.schemas import DailyQuote, Financial, StockInfo, Market


class YFinanceProvider(BaseProvider):
    """YFinance数据源（美股）"""

    def _parse_symbol(self, symbol: str) -> tuple[str, Market]:
        """解析股票代码"""
        if symbol.endswith(".US"):
            return symbol[:-3], Market.US_STOCK
        if symbol.endswith(".HK"):
            return symbol.replace(".HK", ".HK"), Market.HK_STOCK  # yfinance格式
        return symbol, Market.US_STOCK

    def get_daily_quotes(self, symbol: str, start: date, end: date) -> list[DailyQuote]:
        """获取日线行情"""
        yf_symbol, _ = self._parse_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(start=start, end=end)

        if df.empty:
            return []

        quotes = []
        for idx, row in df.iterrows():
            trade_date = idx.date()
            quotes.append(DailyQuote(
                symbol=symbol,
                trade_date=trade_date,
                open=Decimal(str(row["Open"])) if row["Open"] else None,
                high=Decimal(str(row["High"])) if row["High"] else None,
                low=Decimal(str(row["Low"])) if row["Low"] else None,
                close=Decimal(str(row["Close"])) if row["Close"] else None,
                volume=int(row["Volume"]) if row["Volume"] else None,
            ))
        return quotes

    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """获取股票基础信息"""
        yf_symbol, market = self._parse_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info

        if not info:
            return None

        return StockInfo(
            symbol=symbol,
            name=info.get("longName") or info.get("shortName") or yf_symbol,
            market=market,
            industry=info.get("industry"),
        )

    def get_financials(self, symbol: str, years: int = 5) -> list[Financial]:
        """获取财务数据"""
        yf_symbol, _ = self._parse_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info

        if not info:
            return []

        return [Financial(
            symbol=symbol,
            report_date=date.today(),
            pe=Decimal(str(info.get("trailingPE", 0))) if info.get("trailingPE") else None,
            pb=Decimal(str(info.get("priceToBook", 0))) if info.get("priceToBook") else None,
            gross_margin=Decimal(str(info.get("grossMargins", 0) * 100)) if info.get("grossMargins") else None,
        )]

    def search_stocks(self, keyword: str) -> list[StockInfo]:
        """搜索股票"""
        # yfinance没有直接搜索API，使用预定义热门股票
        popular = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "WMT"]
        results = []
        for sym in popular:
            if keyword.upper() in sym:
                try:
                    info = yf.Ticker(sym).info
                    results.append(StockInfo(
                        symbol=f"{sym}.US",
                        name=info.get("longName", sym),
                        market=Market.US_STOCK,
                    ))
                except Exception:
                    pass
        return results
