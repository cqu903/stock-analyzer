"""持仓服务"""

from datetime import date
from decimal import Decimal

from loguru import logger

from src.data.repository import Repository
from src.models.portfolio import AccountSummary, Position, Transaction


class PositionService:
    """持仓服务"""

    def __init__(self, repo: Repository):
        self.repo = repo

    def get_positions(self, account_id: int) -> list[Position]:
        """获取持仓列表"""
        transactions = self.repo.get_transactions(account_id, limit=10000)

        # 按股票分组
        position_map = {}
        for tx in transactions:
            symbol = tx.symbol
            if symbol not in position_map:
                position_map[symbol] = {
                    "shares": 0,
                    "cost": Decimal("0"),
                    "transactions": [],
                }
            position_map[symbol]["transactions"].append(tx)

        # 计算持仓
        positions = []
        for symbol, data in position_map.items():
            pos = self._calculate_position(account_id, symbol, data["transactions"])
            if pos and pos.shares > 0:
                positions.append(pos)

        return positions

    def _calculate_position(
        self, account_id: int, symbol: str, transactions: list[Transaction]
    ) -> Position | None:
        """计算单只股票的持仓"""
        total_shares = 0
        total_cost = Decimal("0")

        # 按日期排序
        sorted_tx = sorted(transactions, key=lambda x: x.trade_date)

        for tx in sorted_tx:
            if tx.trade_type in ("买入", "BUY"):
                total_shares += tx.shares
                total_cost += tx.amount + tx.fee
            else:
                # 卖出，使用平均成本法计算成本
                avg_cost = total_cost / total_shares if total_shares > 0 else Decimal("0")
                cost_to_reduce = avg_cost * tx.shares
                total_cost -= cost_to_reduce
                total_shares -= tx.shares

        if total_shares <= 0:
            return None

        # 获取当前价格
        latest_quote = self.repo.get_latest_quote(symbol)
        current_price = latest_quote.close if latest_quote else Decimal("0")

        market_value = current_price * total_shares
        cost_value = total_cost
        unrealized_pnl = market_value - cost_value
        unrealized_pnl_pct = (
            (unrealized_pnl / cost_value * 100) if cost_value > 0 else Decimal("0")
        )

        # 获取股票名称
        stock_info = self.repo.get_stock_info(symbol)
        name = stock_info.name if stock_info else symbol

        return Position(
            symbol=symbol,
            name=name,
            shares=total_shares,
            avg_cost=cost_value / total_shares,
            current_price=current_price,
            market_value=market_value,
            cost_value=cost_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
        )

    def get_account_summary(self, account_id: int) -> AccountSummary:
        """获取账户汇总"""
        account = self.repo.get_account(account_id)
        if not account:
            raise ValueError(f"账户不存在: {account_id}")

        positions = self.get_positions(account_id)

        cash = account.current_cash
        positions_value = sum(p.market_value for p in positions)
        total_assets = cash + positions_value
        total_cost = sum(p.cost_value for p in positions)
        total_pnl = sum(p.unrealized_pnl for p in positions)
        total_pnl_pct = (
            (total_pnl / total_cost * 100) if total_cost > 0 else Decimal("0")
        )

        return AccountSummary(
            total_assets=total_assets,
            cash=cash,
            positions_value=positions_value,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            total_cost=total_cost,
        )
