# 组合管理与量化选股功能实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为股票分析平台添加组合管理（多账户持仓跟踪）和量化选股（预设策略筛选）功能。

**Architecture:** 新增 `src/portfolio/` 和 `src/screening/` 模块，新增2张数据库表，新增2个Streamlit页面。遵循现有代码模式和分层架构。

**Tech Stack:** Python 3.11+, Streamlit, SQLAlchemy, Pydantic, pytest

---

## Phase 1: 组合管理 - 数据层

### Task 1: 更新数据库表结构

**Files:**
- Modify: `sql/init.sql`

**Step 1: 添加账户表和交易记录表**

在 `sql/init.sql` 文件末尾添加以下内容：

```sql
-- 账户表
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '账户名称',
    account_type VARCHAR(20) DEFAULT '证券账户' COMMENT '账户类型',
    initial_capital DECIMAL(18,2) NOT NULL COMMENT '初始资金',
    current_cash DECIMAL(18,2) NOT NULL COMMENT '当前现金',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 交易记录表
CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL COMMENT '所属账户',
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_type ENUM('买入', '卖出') NOT NULL COMMENT '交易类型',
    shares INT NOT NULL COMMENT '成交数量',
    price DECIMAL(10,3) NOT NULL COMMENT '成交价格',
    amount DECIMAL(18,2) NOT NULL COMMENT '成交金额',
    fee DECIMAL(10,2) DEFAULT 0 COMMENT '手续费',
    trade_date DATE NOT NULL COMMENT '交易日期',
    notes TEXT COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    INDEX idx_account_date (account_id, trade_date),
    INDEX idx_symbol (symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Step 2: 提交**

```bash
git add sql/init.sql
git commit -m "feat: 添加组合管理数据库表结构"
```

---

### Task 2: 添加组合管理数据模型

**Files:**
- Create: `src/models/portfolio.py`
- Modify: `src/models/__init__.py`
- Create: `tests/test_portfolio_models.py`

**Step 1: 写测试 tests/test_portfolio_models.py**

```python
import pytest
from datetime import date, datetime
from decimal import Decimal

from src.models.portfolio import (
    Account, AccountType, Transaction, TradeType,
    Position, AccountSummary
)


def test_account_creation():
    """测试账户创建"""
    account = Account(
        id=1,
        name="A股账户",
        account_type=AccountType.SECURITIES,
        initial_capital=Decimal("100000"),
        current_cash=Decimal("50000"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert account.name == "A股账户"
    assert account.initial_capital == Decimal("100000")


def test_transaction_creation():
    """测试交易记录创建"""
    transaction = Transaction(
        id=1,
        account_id=1,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.5"),
        amount=Decimal("10500"),
        fee=Decimal("5"),
        trade_date=date.today(),
    )
    assert transaction.symbol == "000001.SZ"
    assert transaction.trade_type == TradeType.BUY


def test_position_calculation():
    """测试持仓计算"""
    position = Position(
        symbol="000001.SZ",
        name="平安银行",
        shares=1000,
        avg_cost=Decimal("10.5"),
        current_price=Decimal("12.0"),
        market_value=Decimal("12000"),
        cost_value=Decimal("10500"),
        unrealized_pnl=Decimal("1500"),
        unrealized_pnl_pct=Decimal("14.29"),
    )
    assert position.unrealized_pnl_pct > 0
```

**Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_portfolio_models.py -v
```

Expected: FAIL - 模块不存在

**Step 3: 实现数据模型 src/models/portfolio.py**

```python
"""组合管理相关数据模型"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


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
```

**Step 4: 更新 src/models/__init__.py**

```python
from .portfolio import (
    Account, AccountType, AccountSummary,
    Position, Transaction, TradeType
)
```

**Step 5: 运行测试确认通过**

```bash
uv run pytest tests/test_portfolio_models.py -v
```

Expected: PASS

**Step 6: 提交**

```bash
git add src/models/portfolio.py src/models/__init__.py tests/test_portfolio_models.py
git commit -m "feat: 添加组合管理数据模型"
```

---

### Task 3: 扩展Repository支持组合管理

**Files:**
- Modify: `src/data/repository.py`
- Create: `tests/test_portfolio_repository.py`

**Step 1: 写测试 tests/test_portfolio_repository.py**

```python
import pytest
from datetime import date, datetime
from decimal import Decimal

from src.data.repository import Repository
from src.models.portfolio import Account, AccountType, Transaction, TradeType


@pytest.fixture
def repo():
    return Repository("sqlite:///:memory:")


def test_create_and_get_account(repo):
    """测试创建和获取账户"""
    account = Account(
        name="测试账户",
        account_type=AccountType.SECURITIES,
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    repo.create_account(account)

    accounts = repo.get_accounts()
    assert len(accounts) == 1
    assert accounts[0].name == "测试账户"


def test_add_and_get_transactions(repo):
    """测试添加和获取交易记录"""
    # 先创建账户
    account = Account(
        name="测试账户",
        initial_capital=Decimal("100000"),
        current_cash=Decimal("100000"),
    )
    account = repo.create_account(account)

    # 添加交易
    transaction = Transaction(
        account_id=account.id,
        symbol="000001.SZ",
        trade_type=TradeType.BUY,
        shares=1000,
        price=Decimal("10.5"),
        amount=Decimal("10500"),
        trade_date=date.today(),
    )
    repo.add_transaction(transaction)

    transactions = repo.get_transactions(account.id)
    assert len(transactions) == 1
    assert transactions[0].symbol == "000001.SZ"
```

**Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_portfolio_repository.py -v
```

Expected: FAIL - 方法不存在

**Step 3: 在 Repository 类中添加组合管理方法**

在 `src/data/repository.py` 的 `Repository` 类中添加以下方法：

```python
# 在类中添加，确保表存在
def _ensure_tables(self):
    # ... 现有代码 ...
    # 添加新表的创建
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL,
            account_type VARCHAR(20) DEFAULT '证券账户',
            initial_capital DECIMAL(18,2) NOT NULL,
            current_cash DECIMAL(18,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INT NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            trade_type VARCHAR(10) NOT NULL,
            shares INT NOT NULL,
            price DECIMAL(10,3) NOT NULL,
            amount DECIMAL(18,2) NOT NULL,
            fee DECIMAL(10,2) DEFAULT 0,
            trade_date DATE NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
        )
    """))
    conn.commit()

# 组合管理方法
def create_account(self, account) -> Account:
    """创建账户"""
    with self.engine.connect() as conn:
        result = conn.execute(text("""
            INSERT INTO accounts (name, account_type, initial_capital, current_cash)
            VALUES (:name, :account_type, :initial_capital, :current_cash)
        """), {
            "name": account.name,
            "account_type": account.account_type.value if isinstance(account.account_type, type) else account.account_type,
            "initial_capital": float(account.initial_capital),
            "current_cash": float(account.current_cash),
        })
        conn.commit()
        account.id = result.lastrowid
        return account

def get_accounts(self) -> list[Account]:
    """获取所有账户"""
    with self.engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM accounts ORDER BY created_at DESC"))
        accounts = []
        for row in result:
            accounts.append(Account(
                id=row[0],
                name=row[1],
                account_type=row[2],
                initial_capital=Decimal(str(row[3])),
                current_cash=Decimal(str(row[4])),
                created_at=row[5],
                updated_at=row[6],
            ))
        return accounts

def get_account(self, account_id: int):
    """获取单个账户"""
    with self.engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM accounts WHERE id = :id"), {"id": account_id})
        row = result.fetchone()
        if row:
            return Account(
                id=row[0],
                name=row[1],
                account_type=row[2],
                initial_capital=Decimal(str(row[3])),
                current_cash=Decimal(str(row[4])),
                created_at=row[5],
                updated_at=row[6],
            )
        return None

def update_account_cash(self, account_id: int, cash_change: Decimal):
    """更新账户现金"""
    with self.engine.connect() as conn:
        conn.execute(text("""
            UPDATE accounts SET current_cash = current_cash + :change,
            updated_at = CURRENT_TIMESTAMP WHERE id = :id
        """), {"change": float(cash_change), "id": account_id})
        conn.commit()

def delete_account(self, account_id: int):
    """删除账户"""
    with self.engine.connect() as conn:
        conn.execute(text("DELETE FROM accounts WHERE id = :id"), {"id": account_id})
        conn.commit()

def add_transaction(self, transaction) -> Transaction:
    """添加交易记录"""
    with self.engine.connect() as conn:
        result = conn.execute(text("""
            INSERT INTO transactions (account_id, symbol, trade_type, shares, price, amount, fee, trade_date, notes)
            VALUES (:account_id, :symbol, :trade_type, :shares, :price, :amount, :fee, :trade_date, :notes)
        """), {
            "account_id": transaction.account_id,
            "symbol": transaction.symbol,
            "trade_type": transaction.trade_type.value if isinstance(transaction.trade_type, type) else transaction.trade_type,
            "shares": transaction.shares,
            "price": float(transaction.price),
            "amount": float(transaction.amount),
            "fee": float(transaction.fee),
            "trade_date": transaction.trade_date,
            "notes": transaction.notes,
        })
        conn.commit()
        transaction.id = result.lastrowid

        # 更新账户现金
        cash_change = -transaction.amount if transaction.trade_type in ("买入", TradeType.BUY) else transaction.amount
        self.update_account_cash(transaction.account_id, cash_change)

        return transaction

def get_transactions(self, account_id: int, limit: int = 100):
    """获取交易记录"""
    with self.engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM transactions WHERE account_id = :account_id
            ORDER BY trade_date DESC, created_at DESC LIMIT :limit
        """), {"account_id": account_id, "limit": limit})
        transactions = []
        for row in result:
            from src.models.portfolio import TradeType
            transactions.append(Transaction(
                id=row[0],
                account_id=row[1],
                symbol=row[2],
                trade_type=TradeType(row[3]),
                shares=row[4],
                price=Decimal(str(row[5])),
                amount=Decimal(str(row[6])),
                fee=Decimal(str(row[7])),
                trade_date=row[8],
                notes=row[9],
                created_at=row[10],
            ))
        return transactions

def get_transactions_by_symbol(self, account_id: int, symbol: str):
    """获取指定股票的交易记录"""
    with self.engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM transactions WHERE account_id = :account_id AND symbol = :symbol
            ORDER BY trade_date ASC
        """), {"account_id": account_id, "symbol": symbol})
        transactions = []
        for row in result:
            from src.models.portfolio import TradeType
            transactions.append(Transaction(
                id=row[0],
                account_id=row[1],
                symbol=row[2],
                trade_type=TradeType(row[3]),
                shares=row[4],
                price=Decimal(str(row[5])),
                amount=Decimal(str(row[6])),
                fee=Decimal(str(row[7])),
                trade_date=row[8],
                notes=row[9],
                created_at=row[10],
            ))
        return transactions
```

**Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_portfolio_repository.py -v
```

Expected: PASS

**Step 5: 提交**

```bash
git add src/data/repository.py tests/test_portfolio_repository.py
git commit -m "feat: 扩展Repository支持组合管理"
```

---

## Phase 2: 组合管理 - 业务逻辑层

### Task 4: 实现账户管理器

**Files:**
- Create: `src/portfolio/__init__.py`
- Create: `src/portfolio/account_manager.py`
- Create: `tests/test_account_manager.py`

**Step 1: 写测试 tests/test_account_manager.py**

```python
import pytest
from decimal import Decimal

from src.data.repository import Repository
from src.portfolio.account_manager import AccountManager
from src.models.portfolio import Account, AccountType


@pytest.fixture
def repo():
    return Repository("sqlite:///:memory:")


@pytest.fixture
def manager(repo):
    return AccountManager(repo)


def test_create_account(manager):
    """测试创建账户"""
    account = manager.create_account(
        name="测试账户",
        initial_capital=Decimal("100000"),
    )
    assert account.id is not None
    assert account.current_cash == Decimal("100000")


def test_get_accounts(manager):
    """测试获取账户列表"""
    manager.create_account("A股账户", Decimal("100000"))
    manager.create_account("港股账户", Decimal("50000"))

    accounts = manager.get_accounts()
    assert len(accounts) == 2
```

**Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_account_manager.py -v
```

Expected: FAIL - 模块不存在

**Step 3: 实现账户管理器 src/portfolio/account_manager.py**

```python
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
```

**Step 4: 创建 src/portfolio/__init__.py**

```python
from .account_manager import AccountManager
from .position_service import PositionService
from .transaction_service import TransactionService

__all__ = ["AccountManager", "PositionService", "TransactionService"]
```

**Step 5: 运行测试确认通过**

```bash
uv run pytest tests/test_account_manager.py -v
```

Expected: PASS

**Step 6: 提交**

```bash
git add src/portfolio/ tests/test_account_manager.py
git commit -m "feat: 实现账户管理器"
```

---

### Task 5: 实现持仓服务

**Files:**
- Create: `src/portfolio/position_service.py`
- Create: `tests/test_position_service.py`

**Step 1: 写测试 tests/test_position_service.py**

```python
import pytest
from datetime import date
from decimal import Decimal

from src.data.repository import Repository
from src.portfolio.account_manager import AccountManager
from src.portfolio.position_service import PositionService
from src.portfolio.transaction_service import TransactionService
from src.models.portfolio import TradeType


@pytest.fixture
def repo():
    return Repository("sqlite:///:memory:")


@pytest.fixture
def account_data(repo):
    manager = AccountManager(repo)
    return manager.create_account("测试账户", Decimal("100000"))


@pytest.fixture
def sample_transactions(repo, account_data):
    tx_service = TransactionService(repo)
    # 买入1000股 @ 10.5
    tx_service.buy_stock(account_data.id, "000001.SZ", 1000, Decimal("10.5"))
    # 再买入500股 @ 11.0
    tx_service.buy_stock(account_data.id, "000001.SZ", 500, Decimal("11.0"))
    return account_data.id


def test_get_positions(sample_transactions, repo):
    """测试获取持仓列表"""
    position_service = PositionService(repo)
    positions = position_service.get_positions(sample_transactions)

    assert len(positions) == 1
    assert positions[0].shares == 1500
    # 平均成本 = (10500 + 5500) / 1500 = 10.67
    assert positions[0].avg_cost > Decimal("10.6")


def test_get_account_summary(sample_transactions, repo):
    """测试获取账户汇总"""
    position_service = PositionService(repo)
    summary = position_service.get_account_summary(sample_transactions)

    assert summary.cash < Decimal("100000")  # 现金减少了
    assert summary.positions_value > 0  # 有持仓市值
```

**Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_position_service.py -v
```

Expected: FAIL - 模块不存在

**Step 3: 实现持仓服务 src/portfolio/position_service.py**

```python
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
```

**Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_position_service.py -v
```

Expected: PASS

**Step 5: 提交**

```bash
git add src/portfolio/position_service.py tests/test_position_service.py
git commit -m "feat: 实现持仓服务"
```

---

### Task 6: 实现交易服务

**Files:**
- Create: `src/portfolio/transaction_service.py`
- Create: `tests/test_transaction_service.py`

**Step 1: 写测试 tests/test_transaction_service.py**

```python
import pytest
from datetime import date
from decimal import Decimal

from src.data.repository import Repository
from src.portfolio.account_manager import AccountManager
from src.portfolio.transaction_service import TransactionService
from src.models.portfolio import TradeType


@pytest.fixture
def repo():
    return Repository("sqlite:///:memory:")


@pytest.fixture
def account_data(repo):
    manager = AccountManager(repo)
    return manager.create_account("测试账户", Decimal("100000"))


def test_buy_stock(account_data, repo):
    """测试买入股票"""
    tx_service = TransactionService(repo)
    result = tx_service.buy_stock(
        account_id=account_data.id,
        symbol="000001.SZ",
        shares=1000,
        price=Decimal("10.5"),
        fee=Decimal("5"),
    )

    assert result is True

    # 验证现金减少
    account = repo.get_account(account_data.id)
    expected_cash = Decimal("100000") - Decimal("10500") - Decimal("5")
    assert account.current_cash == expected_cash


def test_sell_stock(account_data, repo):
    """测试卖出股票"""
    tx_service = TransactionService(repo)

    # 先买入
    tx_service.buy_stock(account_data.id, "000001.SZ", 1000, Decimal("10.5"))

    # 再卖出
    result = tx_service.sell_stock(
        account_id=account_data.id,
        symbol="000001.SZ",
        shares=500,
        price=Decimal("12.0"),
        fee=Decimal("5"),
    )

    assert result is True
```

**Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_transaction_service.py -v
```

Expected: FAIL - 模块不存在

**Step 3: 实现交易服务 src/portfolio/transaction_service.py**

```python
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
```

**Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_transaction_service.py -v
```

Expected: PASS

**Step 5: 提交**

```bash
git add src/portfolio/transaction_service.py tests/test_transaction_service.py
git commit -m "feat: 实现交易服务"
```

---

## Phase 3: 组合管理 - Streamlit页面

### Task 7: 创建组合管理页面

**Files:**
- Create: `src/pages/6_💼_组合管理.py`

**Step 1: 实现组合管理页面**

```python
"""组合管理页面"""

from decimal import Decimal

import streamlit as st

from config.settings import get_settings
from src.data.repository import Repository
from src.models.portfolio import AccountType, TradeType
from src.portfolio.account_manager import AccountManager
from src.portfolio.position_service import PositionService
from src.portfolio.transaction_service import TransactionService

st.set_page_config(page_title="组合管理", page_icon="💼", layout="wide")

settings = get_settings()
repo = Repository(settings.database_url)
account_manager = AccountManager(repo)
position_service = PositionService(repo)
transaction_service = TransactionService(repo)

st.title("💼 组合管理")

# 初始化session state
if "selected_account_id" not in st.session_state:
    st.session_state.selected_account_id = None

# 获取所有账户
accounts = account_manager.get_accounts()

if not accounts:
    st.info("暂无账户，请先创建账户")
    with st.expander("创建新账户", expanded=True):
        name = st.text_input("账户名称")
        initial_capital = st.number_input("初始资金", min_value=0.0, step=1000.0, format="%.2f")
        account_type = st.selectbox("账户类型", options=[AccountType.SECURITIES, AccountType.SIMULATION])

        if st.button("创建账户", type="primary"):
            if name and initial_capital > 0:
                account = account_manager.create_account(
                    name=name,
                    initial_capital=Decimal(str(initial_capital)),
                    account_type=account_type,
                )
                st.success(f"账户创建成功！ID: {account.id}")
                st.rerun()
else:
    # 账户选择
    account_options = {f"{acc.name} (ID: {acc.id})": acc.id for acc in accounts}
    selected = st.selectbox(
        "选择账户",
        options=list(account_options.keys()),
        index=list(account_options.values()).index(st.session_state.selected_account_id) if st.session_state.selected_account_id in account_options.values() else 0,
    )
    account_id = account_options[selected]
    st.session_state.selected_account_id = account_id

    # 获取当前账户
    account = account_manager.get_account(account_id)

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("➕ 新建账户"):
            st.session_state.show_create_account = True

    with col2:
        if st.button("🗑️ 删除账户"):
            account_manager.delete_account(account_id)
            st.session_state.selected_account_id = None
            st.success("账户已删除")
            st.rerun()

    # 创建账户对话框
    if st.session_state.get("show_create_account"):
        with st.expander("创建新账户", expanded=True):
            name = st.text_input("账户名称", key="new_account_name")
            initial_capital = st.number_input("初始资金", min_value=0.0, step=1000.0, format="%.2f", key="new_account_capital")
            account_type = st.selectbox("账户类型", options=[AccountType.SECURITIES, AccountType.SIMULATION], key="new_account_type")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("创建", type="primary", key="create_account_btn"):
                    if name and initial_capital > 0:
                        account_manager.create_account(name, Decimal(str(initial_capital)), account_type)
                        st.success("账户创建成功！")
                        st.session_state.show_create_account = False
                        st.rerun()
            with col_b:
                if st.button("取消", key="cancel_account_btn"):
                    st.session_state.show_create_account = False
                    st.rerun()

    st.markdown("---")

    # 账户概览
    summary = position_service.get_account_summary(account_id)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("总资产", f"¥{summary.total_assets:,.2f}")
    with col2:
        st.metric("现金", f"¥{summary.cash:,.2f}")
    with col3:
        st.metric("持仓市值", f"¥{summary.positions_value:,.2f}")
    with col4:
        delta_color = "normal" if summary.total_pnl >= 0 else "inverse"
        st.metric("总盈亏", f"¥{summary.total_pnl:,.2f}", delta=f"{summary.total_pnl_pct:.2f}%", delta_color=delta_color)
    with col5:
        st.metric("持仓成本", f"¥{summary.total_cost:,.2f}")

    st.markdown("---")

    # 持仓列表
    st.subheader("📊 持仓列表")
    positions = position_service.get_positions(account_id)

    if positions:
        position_data = []
        for p in positions:
            pnl_color = "🟢" if p.unrealized_pnl >= 0 else "🔴"
            position_data.append({
                "股票": f"{p.symbol}\\n{p.name}",
                "持仓": f"{p.shares:,}",
                "成本价": f"¥{p.avg_cost:.2f}",
                "现价": f"¥{p.current_price:.2f}",
                "市值": f"¥{p.market_value:,.2f}",
                "盈亏": f"{pnl_color} ¥{p.unrealized_pnl:,.2f}",
                "盈亏%": f"{p.unrealized_pnl_pct:+.2f}%",
            })

        st.dataframe(
            position_data,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("暂无持仓")

    # 添加交易
    st.markdown("---")
    st.subheader("📝 添加交易")

    with st.expander("买入/卖出股票", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            tx_type = st.radio("交易类型", options=["买入", "卖出"], horizontal=True)
            symbol = st.text_input("股票代码", placeholder="如: 000001.SZ")

        with col2:
            shares = st.number_input("数量", min_value=1, step=100)
            price = st.number_input("价格", min_value=0.01, step=0.01, format="%.2f")

        with col3:
            fee = st.number_input("手续费", min_value=0.0, step=1.0, format="%.2f", value=0.0)
            trade_date = st.date_input("交易日期")

        if st.button("确认交易", type="primary", use_container_width=True):
            if symbol and shares > 0 and price > 0:
                try:
                    if tx_type == "买入":
                        transaction_service.buy_stock(account_id, symbol, shares, Decimal(str(price)), Decimal(str(fee)))
                        st.success(f"买入 {symbol} {shares}股 @{price} 成功")
                    else:
                        transaction_service.sell_stock(account_id, symbol, shares, Decimal(str(price)), Decimal(str(fee)))
                        st.success(f"卖出 {symbol} {shares}股 @{price} 成功")
                    st.rerun()
                except Exception as e:
                    st.error(f"交易失败: {e}")
            else:
                st.warning("请填写完整的交易信息")

    # 交易记录
    st.markdown("---")
    st.subheader("📋 交易记录")

    transactions = transaction_service.get_transactions(account_id, limit=50)

    if transactions:
        tx_data = []
        for tx in reversed(transactions):
            type_emoji = "🟢" if tx.trade_type == TradeType.BUY else "🔴"
            tx_data.append({
                "日期": tx.trade_date.strftime("%Y-%m-%d"),
                "股票": tx.symbol,
                "类型": f"{type_emoji} {tx.trade_type}",
                "数量": f"{tx.shares:,}",
                "价格": f"¥{tx.price:.2f}",
                "金额": f"¥{tx.amount:,.2f}",
            })

        st.dataframe(
            tx_data,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("暂无交易记录")
```

**Step 2: 更新 src/app.py 添加页面链接**

在首页的快速导航中添加组合管理链接（如果还没有的话）。

**Step 3: 提交**

```bash
git add src/pages/6_💼_组合管理.py
git commit -m "feat: 创建组合管理页面"
```

---

## Phase 4: 量化选股 - 数据层

### Task 8: 添加量化选股数据模型

**Files:**
- Create: `src/models/screening.py`
- Modify: `src/models/__init__.py`
- Create: `tests/test_screening_models.py`

**Step 1: 写测试 tests/test_screening_models.py**

```python
import pytest

from src.models.screening import Strategy, ScreenResult


def test_strategy():
    """测试策略模型"""
    strategy = Strategy(
        id="value",
        name="价值投资",
        description="低PE、低PB",
        category="价值",
        params={"max_pe": 15, "max_pb": 2},
    )
    assert strategy.id == "value"
    assert strategy.params["max_pe"] == 15


def test_screen_result():
    """测试筛选结果模型"""
    result = ScreenResult(
        symbol="000001.SZ",
        name="平安银行",
        score=85.5,
        match_details={"pe": 5.2, "pb": 0.8},
        current_price=None,
    )
    assert result.score == 85.5
```

**Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_screening_models.py -v
```

Expected: FAIL - 模块不存在

**Step 3: 实现数据模型 src/models/screening.py**

```python
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
```

**Step 4: 更新 src/models/__init__.py**

```python
from .screening import ScreenResult, Strategy
```

**Step 5: 运行测试确认通过**

```bash
uv run pytest tests/test_screening_models.py -v
```

Expected: PASS

**Step 6: 提交**

```bash
git add src/models/screening.py src/models/__init__.py tests/test_screening_models.py
git commit -m "feat: 添加量化选股数据模型"
```

---

## Phase 5: 量化选股 - 业务逻辑层

### Task 9: 实现策略注册表

**Files:**
- Create: `src/screening/__init__.py`
- Create: `src/screening/strategies.py`
- Create: `tests/test_strategies.py`

**Step 1: 写测试 tests/test_strategies.py**

```python
import pytest

from src.screening.strategies import StrategyRegistry


def test_get_all_strategies():
    """测试获取所有策略"""
    strategies = StrategyRegistry.get_all_strategies()
    assert len(strategies) >= 4

    strategy_ids = [s.id for s in strategies]
    assert "value" in strategy_ids
    assert "growth" in strategy_ids
    assert "low_pe" in strategy_ids
    assert "momentum" in strategy_ids


def test_get_strategy():
    """测试获取单个策略"""
    strategy = StrategyRegistry.get_strategy("value")
    assert strategy is not None
    assert strategy.name == "价值投资"
    assert "max_pe" in strategy.params


def test_get_invalid_strategy():
    """测试获取不存在的策略"""
    strategy = StrategyRegistry.get_strategy("invalid")
    assert strategy is None
```

**Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_strategies.py -v
```

Expected: FAIL - 模块不存在

**Step 3: 实现策略注册表 src/screening/strategies.py**

```python
"""策略注册表"""

from src.models.screening import Strategy


class StrategyRegistry:
    """策略注册表，内置预设策略"""

    _strategies: list[Strategy] = [
        Strategy(
            id="value",
            name="价值投资",
            description="低PE、低PB、高股息",
            category="价值",
            params={
                "max_pe": 15,
                "max_pb": 2,
                "min_dividend_yield": 3,
            },
        ),
        Strategy(
            id="growth",
            name="成长股",
            description="高营收增长、高利润增长",
            category="成长",
            params={
                "min_revenue_growth": 20,
                "min_profit_growth": 15,
                "min_roe": 10,
            },
        ),
        Strategy(
            id="low_pe",
            name="低估值",
            description="PE低于设定值",
            category="价值",
            params={
                "max_pe": 10,
            },
        ),
        Strategy(
            id="momentum",
            name="动量策略",
            description="股价突破均线、成交量放大",
            category="技术",
            params={
                "ma_period": 20,
                "volume_multiplier": 1.5,
            },
        ),
    ]

    @classmethod
    def get_all_strategies(cls) -> list[Strategy]:
        """获取所有策略"""
        return cls._strategies.copy()

    @classmethod
    def get_strategy(cls, strategy_id: str) -> Strategy | None:
        """获取指定策略"""
        for strategy in cls._strategies:
            if strategy.id == strategy_id:
                return strategy
        return None
```

**Step 4: 创建 src/screening/__init__.py**

```python
from .screener import StockScreener
from .strategies import StrategyRegistry

__all__ = ["StrategyRegistry", "StockScreener"]
```

**Step 5: 运行测试确认通过**

```bash
uv run pytest tests/test_strategies.py -v
```

Expected: PASS

**Step 6: 提交**

```bash
git add src/screening/ tests/test_strategies.py
git commit -m "feat: 实现策略注册表"
```

---

### Task 10: 实现选股引擎

**Files:**
- Create: `src/screening/screener.py`
- Create: `tests/test_screener.py`

**Step 1: 写测试 tests/test_screener.py**

```python
import pytest

from src.data.repository import Repository
from src.screening.screener import StockScreener


@pytest.fixture
def repo():
    return Repository("sqlite:///:memory:")


@pytest.fixture
def screener(repo):
    return StockScreener(repo)


def test_screen_low_pe_strategy(screener, repo):
    """测试低PE策略筛选"""
    # 先添加一些测试数据
    from src.models.schemas import StockInfo, DailyQuote, Market
    from datetime import date
    from decimal import Decimal

    # 添加股票信息
    repo.save_stock_info(StockInfo(symbol="000001.SZ", name="平安银行", market=Market.A_STOCK))
    repo.save_stock_info(StockInfo(symbol="600519.SH", name="贵州茅台", market=Market.A_STOCK))

    # 添加行情数据
    today = date.today()
    repo.save_quotes([
        DailyQuote(symbol="000001.SZ", trade_date=today, open=Decimal("10"), high=Decimal("11"),
                   low=Decimal("9"), close=Decimal("10.5"), volume=1000000, pre_close=Decimal("10")),
    ])

    results = screener.screen("low_pe", {"max_pe": 10}, Market.A_STOCK)
    # 验证返回结果是列表
    assert isinstance(results, list)
```

**Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_screener.py -v
```

Expected: FAIL - 模块不存在

**Step 3: 实现选股引擎 src/screening/screener.py**

```python
"""选股引擎"""

from decimal import Decimal

from loguru import logger

from src.analysis.fundamental import FundamentalAnalyzer
from src.analysis.technical import TechnicalAnalyzer
from src.data.repository import Repository
from src.models.schemas import Market, StockInfo
from src.models.screening import ScreenResult, Strategy
from src.screening.strategies import StrategyRegistry


class StockScreener:
    """选股引擎"""

    def __init__(self, repo: Repository):
        self.repo = repo
        self.fundamental_analyzer = FundamentalAnalyzer(repo)
        self.technical_analyzer = TechnicalAnalyzer(repo)

    def screen(
        self, strategy_id: str, params: dict, market: Market
    ) -> list[ScreenResult]:
        """执行选股策略"""
        strategy = StrategyRegistry.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 合并默认参数
        merged_params = {**strategy.params, **params}

        # 获取股票池（这里简单获取所有股票，实际应用中可以优化）
        stocks = self._get_stock_pool(market)

        # 根据策略类型筛选
        if strategy_id == "value":
            return self._screen_value_strategy(stocks, merged_params)
        elif strategy_id == "growth":
            return self._screen_growth_strategy(stocks, merged_params)
        elif strategy_id == "low_pe":
            return self._screen_low_pe_strategy(stocks, merged_params)
        elif strategy_id == "momentum":
            return self._screen_momentum_strategy(stocks, merged_params)
        else:
            return []

    def _get_stock_pool(self, market: Market) -> list[StockInfo]:
        """获取股票池"""
        # 这里简单返回自选股作为股票池
        # 实际应用中可以获取更多股票
        watchlist = self.repo.get_watchlist()
        stocks = []
        for item in watchlist:
            info = self.repo.get_stock_info(item.symbol)
            if info and info.market == market:
                stocks.append(info)
        return stocks

    def _screen_value_strategy(
        self, stocks: list[StockInfo], params: dict
    ) -> list[ScreenResult]:
        """价值投资策略筛选"""
        results = []
        max_pe = params.get("max_pe", 15)
        max_pb = params.get("max_pb", 2)

        for stock in stocks:
            try:
                # 获取财务数据
                financials = self.repo.get_financials(stock.symbol, years=1)
                if not financials:
                    continue

                latest = financials[-1]
                pe = float(latest.pe) if latest.pe else None
                pb = float(latest.pb) if latest.pb else None

                # 筛选条件
                if pe and pb and pe <= max_pe and pb <= max_pb:
                    score = self._calculate_value_score(pe, pb, params)
                    results.append(
                        ScreenResult(
                            symbol=stock.symbol,
                            name=stock.name,
                            score=score,
                            match_details={"pe": pe, "pb": pb},
                            current_price=None,
                        )
                    )
            except Exception as e:
                logger.warning(f"分析 {stock.symbol} 失败: {e}")
                continue

        return sorted(results, key=lambda x: x.score, reverse=True)

    def _calculate_value_score(self, pe: float, pb: float, params: dict) -> float:
        """计算价值投资评分"""
        max_pe = params.get("max_pe", 15)
        max_pb = params.get("max_pb", 2)

        # PE越低越好
        pe_score = (1 - pe / max_pe) * 50
        # PB越低越好
        pb_score = (1 - pb / max_pb) * 50

        return min(100, max(0, pe_score + pb_score))

    def _screen_growth_strategy(
        self, stocks: list[StockInfo], params: dict
    ) -> list[ScreenResult]:
        """成长股策略筛选"""
        results = []
        min_revenue_growth = params.get("min_revenue_growth", 20)
        min_profit_growth = params.get("min_profit_growth", 15)

        for stock in stocks:
            try:
                report = self.fundamental_analyzer.analyze(stock.symbol, years=3)
                if not report.growth:
                    continue

                revenue_yoy = (
                    float(report.growth.revenue_yoy) if report.growth.revenue_yoy else 0
                )
                profit_yoy = (
                    float(report.growth.profit_yoy) if report.growth.profit_yoy else 0
                )

                if revenue_yoy >= min_revenue_growth and profit_yoy >= min_profit_growth:
                    score = (revenue_yoy + profit_yoy) / 2
                    results.append(
                        ScreenResult(
                            symbol=stock.symbol,
                            name=stock.name,
                            score=min(100, score),
                            match_details={
                                "revenue_yoy": revenue_yoy,
                                "profit_yoy": profit_yoy,
                            },
                            current_price=None,
                        )
                    )
            except Exception as e:
                logger.warning(f"分析 {stock.symbol} 失败: {e}")
                continue

        return sorted(results, key=lambda x: x.score, reverse=True)

    def _screen_low_pe_strategy(
        self, stocks: list[StockInfo], params: dict
    ) -> list[ScreenResult]:
        """低PE策略筛选"""
        results = []
        max_pe = params.get("max_pe", 10)

        for stock in stocks:
            try:
                financials = self.repo.get_financials(stock.symbol, years=1)
                if not financials:
                    continue

                latest = financials[-1]
                pe = float(latest.pe) if latest.pe else None

                if pe and pe <= max_pe:
                    # PE越低分数越高
                    score = max(0, 100 - pe * 5)
                    results.append(
                        ScreenResult(
                            symbol=stock.symbol,
                            name=stock.name,
                            score=score,
                            match_details={"pe": pe},
                            current_price=None,
                        )
                    )
            except Exception as e:
                logger.warning(f"分析 {stock.symbol} 失败: {e}")
                continue

        return sorted(results, key=lambda x: x.score, reverse=True)

    def _screen_momentum_strategy(
        self, stocks: list[StockInfo], params: dict
    ) -> list[ScreenResult]:
        """动量策略筛选"""
        results = []
        ma_period = params.get("ma_period", 20)

        for stock in stocks:
            try:
                report = self.technical_analyzer.analyze(stock.symbol, days=60)
                if not report.trend or not report.indicators:
                    continue

                # 获取当前价格
                quote = self.repo.get_latest_quote(stock.symbol)
                if not quote:
                    continue

                current_price = float(quote.close)

                # 获取对应的MA值
                ma_value = None
                if ma_period == 5 and report.indicators.ma5:
                    ma_value = float(report.indicators.ma5)
                elif ma_period == 20 and report.indicators.ma20:
                    ma_value = float(report.indicators.ma20)
                elif ma_period == 60 and report.indicators.ma60:
                    ma_value = float(report.indicators.ma60)

                if ma_value and current_price > ma_value:
                    # 突破均线，计算分数
                    score = min(100, (current_price / ma_value - 1) * 200 + 50)
                    results.append(
                        ScreenResult(
                            symbol=stock.symbol,
                            name=stock.name,
                            score=score,
                            match_details={
                                "current_price": current_price,
                                f"ma{ma_period}": ma_value,
                            },
                            current_price=Decimal(str(current_price)),
                        )
                    )
            except Exception as e:
                logger.warning(f"分析 {stock.symbol} 失败: {e}")
                continue

        return sorted(results, key=lambda x: x.score, reverse=True)
```

**Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_screener.py -v
```

Expected: PASS

**Step 5: 提交**

```bash
git add src/screening/screener.py tests/test_screener.py
git commit -m "feat: 实现选股引擎"
```

---

## Phase 6: 量化选股 - Streamlit页面

### Task 11: 创建量化选股页面

**Files:**
- Create: `src/pages/7_🔍_量化选股.py`

**Step 1: 实现量化选股页面**

```python
"""量化选股页面"""

from decimal import Decimal

import streamlit as st

from config.settings import get_settings
from src.data.repository import Repository
from src.models.schemas import Market
from src.screening.screener import StockScreener
from src.screening.strategies import StrategyRegistry

st.set_page_config(page_title="量化选股", page_icon="🔍", layout="wide")

settings = get_settings()
repo = Repository(settings.database_url)
screener = StockScreener(repo)

st.title("🔍 量化选股")

# 获取所有策略
strategies = StrategyRegistry.get_all_strategies()

# 初始化session state
if "selected_strategy" not in st.session_state:
    st.session_state.selected_strategy = strategies[0].id if strategies else None
if "screening_results" not in st.session_state:
    st.session_state.screening_results = None

# 策略选择
st.subheader("选择策略")

# 创建策略选择列
strategy_cols = st.columns(len(strategies))

for i, strategy in enumerate(strategies):
    with strategy_cols[i % 4]:
        is_selected = st.session_state.selected_strategy == strategy.id
        if st.button(
            f"**{strategy.name}**\\n{strategy.description}",
            key=f"strategy_{strategy.id}",
            type="primary" if is_selected else "secondary",
            use_container_width=True,
        ):
            st.session_state.selected_strategy = strategy.id
            st.rerun()

# 获取当前策略
current_strategy = StrategyRegistry.get_strategy(st.session_state.selected_strategy)

if current_strategy:
    st.markdown("---")

    # 参数调整
    st.subheader("参数调整")

    # 根据策略动态显示参数
    params = {}
    param_cols = st.columns(min(4, len(current_strategy.params)))

    for i, (param_name, default_value) in enumerate(current_strategy.params.items()):
        with param_cols[i]:
            if isinstance(default_value, int) or isinstance(default_value, float):
                value = st.number_input(
                    param_name,
                    value=float(default_value),
                    step=1.0,
                    key=f"param_{param_name}",
                )
                params[param_name] = value
            else:
                value = st.text_input(param_name, value=str(default_value), key=f"param_{param_name}")
                params[param_name] = value

    # 市场选择
    market = st.selectbox("筛选市场", options=[Market.A_STOCK, Market.HK_STOCK, Market.US_STOCK])

    col1, col2 = st.columns([1, 4])

    with col1:
        if st.button("开始筛选", type="primary", use_container_width=True):
            with st.spinner("筛选中..."):
                try:
                    results = screener.screen(st.session_state.selected_strategy, params, market)
                    st.session_state.screening_results = results
                    st.success(f"筛选完成，共找到 {len(results)} 只股票")
                except Exception as e:
                    st.error(f"筛选失败: {e}")
                    st.session_state.screening_results = None

    # 显示结果
    if st.session_state.screening_results is not None:
        st.markdown("---")
        st.subheader(f"筛选结果（共 {len(st.session_state.screening_results)} 只）")

        results = st.session_state.screening_results

        if results:
            # 批量操作
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 批量加入自选股"):
                    added_count = 0
                    for r in results:
                        try:
                            repo.add_to_watchlist(r.symbol)
                            added_count += 1
                        except Exception:
                            pass  # 可能已存在
                    st.success(f"已添加 {added_count} 只股票到自选股")

            # 结果表格
            result_data = []
            for r in results:
                # 匹配度星级
                stars = "⭐" * int(r.score / 20)
                if r.score >= 80:
                    stars += " 推荐"
                elif r.score >= 60:
                    stars += " 良好"
                else:
                    stars += " 一般"

                # 匹配详情
                details_str = ", ".join([f"{k}={v}" for k, v in r.match_details.items()])

                result_data.append({
                    "代码": r.symbol,
                    "名称": r.name,
                    "匹配度": f"{stars}",
                    "评分": f"{r.score:.1f}",
                    "指标详情": details_str,
                    "操作": f"[📌 加入]",
                })

            st.dataframe(
                result_data,
                use_container_width=True,
                hide_index=True,
            )

            # 单只股票操作
            st.markdown("---")
            st.subheader("单只股票操作")

            selected_symbol = st.selectbox(
                "选择股票",
                options=[r.symbol for r in results],
                format_func=lambda x: f"{x} - {next(r.name for r in results if r.symbol == x)}",
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("加入自选股", type="primary"):
                    repo.add_to_watchlist(selected_symbol)
                    st.success(f"已将 {selected_symbol} 加入自选股")

            with col2:
                if st.button("查看技术分析"):
                    st.session_state.analyze_symbol = selected_symbol
                    st.info("请切换到「技术分析」页面查看")

            with col3:
                if st.button("查看基本面分析"):
                    st.session_state.analyze_symbol = selected_symbol
                    st.info("请切换到「基本面」页面查看")

        else:
            st.info("未找到符合条件的股票")
```

**Step 2: 提交**

```bash
git add src/pages/7_🔍_量化选股.py
git commit -m "feat: 创建量化选股页面"
```

---

## Phase 7: 整合测试

### Task 12: 运行所有测试

**Step 1: 运行完整测试套件**

```bash
uv run pytest tests/ -v
```

Expected: 所有测试通过

**Step 2: 生成覆盖率报告**

```bash
uv run pytest --cov=src/portfolio --cov=src/screening --cov-report=html
```

**Step 3: 启动应用验证**

```bash
uv run streamlit run src/app.py
```

验证以下功能：
1. 组合管理页面可以创建账户、添加交易、查看持仓
2. 量化选股页面可以选择策略、调整参数、筛选股票

**Step 4: 提交**

```bash
git add .
git commit -m "feat: 完成组合管理与量化选股功能"
```

---

## 完成清单

- [ ] Task 1: 更新数据库表结构
- [ ] Task 2: 添加组合管理数据模型
- [ ] Task 3: 扩展Repository支持组合管理
- [ ] Task 4: 实现账户管理器
- [ ] Task 5: 实现持仓服务
- [ ] Task 6: 实现交易服务
- [ ] Task 7: 创建组合管理页面
- [ ] Task 8: 添加量化选股数据模型
- [ ] Task 9: 实现策略注册表
- [ ] Task 10: 实现选股引擎
- [ ] Task 11: 创建量化选股页面
- [ ] Task 12: 整合测试
