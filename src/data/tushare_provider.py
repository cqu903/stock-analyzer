"""
Tushare数据源（A股）
提供A股市场股票行情和财务数据
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

import tushare as ts
from loguru import logger

from src.data.base import BaseProvider
from src.models.schemas import DailyQuote, Financial, StockInfo, Market


class TushareProvider(BaseProvider):
    """Tushare数据源（A股）"""

    def __init__(self, token: str):
        self.pro = ts.pro_api(token)

    def _parse_symbol(self, symbol: str) -> tuple[str, Market]:
        """解析股票代码

        Args:
            symbol: 股票代码，支持带后缀(如000001.SZ)或不带后缀(如000001)

        Returns:
            (ts_code, market): Tushare格式的代码和市场类型
        """
        if "." in symbol:
            code, suffix = symbol.split(".")
            if suffix in ("SH", "SZ", "BJ"):
                return symbol, Market.A_STOCK
        # 默认添加后缀
        if symbol.startswith("6"):
            return f"{symbol}.SH", Market.A_STOCK
        elif symbol.startswith(("0", "3")):
            return f"{symbol}.SZ", Market.A_STOCK
        elif symbol.startswith(("4", "8")):
            return f"{symbol}.BJ", Market.A_STOCK
        return symbol, Market.A_STOCK

    def _to_stock_info(self, row: dict) -> StockInfo:
        """将Tushare返回的数据行转换为StockInfo

        Args:
            row: Tushare返回的数据行

        Returns:
            StockInfo对象
        """
        list_date = None
        if row.get("list_date"):
            date_str = str(row["list_date"])
            list_date = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))

        return StockInfo(
            symbol=row["ts_code"],
            name=row["name"],
            market=Market.A_STOCK,
            industry=row.get("industry"),
            list_date=list_date,
        )

    def get_daily_quotes(self, symbol: str, start: date, end: date) -> list[DailyQuote]:
        """获取日线行情

        Args:
            symbol: 股票代码
            start: 开始日期
            end: 结束日期

        Returns:
            日线行情列表
        """
        ts_code, _ = self._parse_symbol(symbol)
        df = self.pro.daily(
            ts_code=ts_code,
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
        )
        if df.empty:
            return []

        quotes = []
        for _, row in df.iterrows():
            trade_date_str = str(row["trade_date"])
            quotes.append(DailyQuote(
                symbol=symbol,
                trade_date=date(int(trade_date_str[:4]), int(trade_date_str[4:6]), int(trade_date_str[6:8])),
                open=Decimal(str(row["open"])) if row["open"] else None,
                high=Decimal(str(row["high"])) if row["high"] else None,
                low=Decimal(str(row["low"])) if row["low"] else None,
                close=Decimal(str(row["close"])) if row["close"] else None,
                volume=int(row["vol"]) if row["vol"] else None,
                amount=Decimal(str(row["amount"])) * 1000 if row["amount"] else None,
                pre_close=Decimal(str(row["pre_close"])) if row["pre_close"] else None,
            ))
        return quotes

    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """获取股票基础信息

        Args:
            symbol: 股票代码

        Returns:
            股票基础信息，不存在则返回None
        """
        ts_code, market = self._parse_symbol(symbol)
        df = self.pro.stock_basic(ts_code=ts_code, fields="ts_code,symbol,name,area,industry,list_date")
        if df.empty:
            return None

        row = df.iloc[0].to_dict()
        list_date = None
        if row.get("list_date"):
            date_str = str(row["list_date"])
            list_date = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))

        return StockInfo(
            symbol=symbol,
            name=row["name"],
            market=market,
            industry=row.get("industry"),
            list_date=list_date,
        )

    def get_financials(self, symbol: str, years: int = 5) -> list[Financial]:
        """获取财务数据

        Args:
            symbol: 股票代码
            years: 获取最近几年的数据

        Returns:
            财务数据列表
        """
        ts_code, _ = self._parse_symbol(symbol)
        start_date = (date.today() - timedelta(days=years * 365)).strftime("%Y%m%d")

        df = self.pro.fina_indicator(ts_code=ts_code, start_date=start_date, fields="ts_code,ann_date,roe,pe,pb,debt_to_assets,grossprofit_margin")

        financials = []
        for _, row in df.iterrows():
            if row["ann_date"]:
                ann_date_str = str(row["ann_date"])
                financials.append(Financial(
                    symbol=symbol,
                    report_date=date(int(ann_date_str[:4]), int(ann_date_str[4:6]), int(ann_date_str[6:8])),
                    roe=Decimal(str(row["roe"])) if row["roe"] else None,
                    pe=Decimal(str(row["pe"])) if row["pe"] else None,
                    pb=Decimal(str(row["pb"])) if row["pb"] else None,
                    debt_ratio=Decimal(str(row["debt_to_assets"])) if row["debt_to_assets"] else None,
                    gross_margin=Decimal(str(row["grossprofit_margin"])) if row["grossprofit_margin"] else None,
                ))
        return financials

    def search_stocks(self, keyword: str) -> list[StockInfo]:
        """搜索股票

        Args:
            keyword: 搜索关键词（股票代码或名称）

        Returns:
            匹配的股票信息列表
        """
        df = self.pro.stock_basic(fields="ts_code,symbol,name,area,industry,list_date")
        df = df[df["name"].str.contains(keyword, na=False)]

        results = []
        for _, row in df.iterrows():
            results.append(StockInfo(
                symbol=row["ts_code"],
                name=row["name"],
                market=Market.A_STOCK,
                industry=row.get("industry"),
            ))
        return results
