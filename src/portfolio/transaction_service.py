"""交易服务"""

from datetime import date
from decimal import Decimal

from loguru import logger

from src.data.repository import Repository
from src.models.portfolio import Transaction, TradeType


class TransactionService:
    """交易服务"""

    def __init__(self, repo: Repository):
        self.repo = repo

    def add_transaction(self, transaction: Transaction) -> Transaction:
        """添加交易记录"""
        return self.repo.add_transaction(transaction)

    def get_transactions(self, account_id: int, limit: int = 100) -> list[Transaction]:
        """获取交易记录"""
        return self.repo.get_transactions(account_id, limit)

    def buy_stock(
        self,
        account_id: int,
        symbol: str,
        shares: int,
        price: Decimal,
        fee: Decimal = Decimal("0"),
    ) -> bool:
        """买入股票"""
        amount = price * shares
        transaction = Transaction(
            account_id=account_id,
            symbol=symbol,
            trade_type=TradeType.BUY,
            shares=shares,
            price=price,
            amount=amount,
            fee=fee,
            trade_date=date.today(),
        )
        self.repo.add_transaction(transaction)
        logger.info(f"买入: {symbol} {shares}股 @{price}")
        return True

    def sell_stock(
        self,
        account_id: int,
        symbol: str,
        shares: int,
        price: Decimal,
        fee: Decimal = Decimal("0"),
    ) -> bool:
        """卖出股票"""
        amount = price * shares
        transaction = Transaction(
            account_id=account_id,
            symbol=symbol,
            trade_type=TradeType.SELL,
            shares=shares,
            price=price,
            amount=amount,
            fee=fee,
            trade_date=date.today(),
        )
        self.repo.add_transaction(transaction)
        logger.info(f"卖出: {symbol} {shares}股 @{price}")
        return True

    def get_transactions_by_symbol(self, account_id: int, symbol: str) -> list[Transaction]:
        """获取指定股票的交易记录"""
        return self.repo.get_transactions_by_symbol(account_id, symbol)
