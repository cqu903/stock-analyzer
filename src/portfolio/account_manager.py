"""账户管理器"""

from decimal import Decimal

from loguru import logger

from src.data.repository import Repository
from src.models.portfolio import Account, AccountType


class AccountManager:
    """账户管理器"""

    def __init__(self, repo: Repository):
        self.repo = repo

    def create_account(
        self,
        name: str,
        initial_capital: Decimal,
        account_type: AccountType = AccountType.SECURITIES,
    ) -> Account:
        """创建账户"""
        account = Account(
            name=name,
            account_type=account_type,
            initial_capital=initial_capital,
            current_cash=initial_capital,
        )
        return self.repo.create_account(account)

    def get_accounts(self) -> list[Account]:
        """获取所有账户"""
        return self.repo.get_accounts()

    def get_account(self, account_id: int) -> Account | None:
        """获取单个账户"""
        return self.repo.get_account(account_id)

    def delete_account(self, account_id: int) -> bool:
        """删除账户"""
        self.repo.delete_account(account_id)
        logger.info(f"删除账户: {account_id}")
        return True
