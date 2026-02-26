# 组合管理与量化选股功能设计

## 概述

本文档定义股票分析平台的两个扩展功能：**组合管理**和**量化选股**。

| 功能 | 方案 | 核心特性 |
|------|------|----------|
| **组合管理** | 完整账户型 | 多账户、多次买卖、持仓成本计算、盈亏统计 |
| **量化选股** | 预设策略型 | 策略模板、参数微调、批量筛选 |

---

## 一、数据模型设计

### 1.1 组合管理数据模型

```python
class AccountType(str, Enum):
    """账户类型"""
    SECURITIES = "证券账户"
    SIMULATION = "模拟账户"

class Account(BaseModel):
    """账户模型"""
    id: int | None = None
    name: str                      # 账户名称，如"A股账户"
    account_type: AccountType      # 账户类型
    initial_capital: Decimal       # 初始资金
    current_cash: Decimal          # 当前现金
    created_at: datetime
    updated_at: datetime

class TradeType(str, Enum):
    """交易类型"""
    BUY = "买入"
    SELL = "卖出"

class Transaction(BaseModel):
    """交易记录模型"""
    id: int | None = None
    account_id: int                # 所属账户
    symbol: str                    # 股票代码
    trade_type: TradeType          # 交易类型
    shares: int                    # 成交数量
    price: Decimal                 # 成交价格
    amount: Decimal                # 成交金额
    fee: Decimal = Decimal('0')    # 手续费
    trade_date: date               # 交易日期
    notes: str | None = None       # 备注
    created_at: datetime

class Position(BaseModel):
    """持仓记录模型（计算得出，不存储）"""
    symbol: str                    # 股票代码
    name: str                      # 股票名称
    shares: int                    # 持仓数量
    avg_cost: Decimal              # 平均成本价
    current_price: Decimal         # 当前价格
    market_value: Decimal          # 市值
    cost_value: Decimal            # 成本值
    unrealized_pnl: Decimal        # 未实现盈亏
    unrealized_pnl_pct: Decimal    # 未实现盈亏百分比

class AccountSummary(BaseModel):
    """账户汇总"""
    total_assets: Decimal          # 总资产
    cash: Decimal                  # 现金
    positions_value: Decimal       # 持仓市值
    total_pnl: Decimal             # 总盈亏
    total_pnl_pct: Decimal         # 总盈亏百分比
```

### 1.2 量化选股数据模型

```python
class Strategy(BaseModel):
    """策略模板模型"""
    id: str                        # 策略ID
    name: str                      # 策略名称
    description: str               # 策略描述
    category: str                  # 分类：价值/成长/技术
    params: dict                   # 可调参数及其默认值

class ScreenResult(BaseModel):
    """筛选结果模型"""
    symbol: str                    # 股票代码
    name: str                      # 股票名称
    score: float                   # 匹配分数 0-100
    match_details: dict            # 各项指标匹配情况
    current_price: Decimal | None  # 当前价格
```

---

## 二、数据库表结构

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

**注意**：持仓数据从交易记录实时计算得出，无需单独存储。

---

## 三、业务逻辑层设计

### 3.1 组合管理服务 (`src/portfolio/`)

```
src/portfolio/
├── __init__.py
├── account_manager.py    # 账户管理
├── position_service.py   # 持仓服务
└── transaction_service.py # 交易服务
```

**AccountManager - 账户管理**
```python
class AccountManager:
    def __init__(self, repo: Repository):
        self.repo = repo

    def create_account(self, name: str, initial_capital: Decimal,
                      account_type: AccountType = AccountType.SECURITIES) -> Account
    def get_accounts(self) -> list[Account]
    def get_account(self, account_id: int) -> Account | None
    def update_cash(self, account_id: int, amount: Decimal) -> bool
    def delete_account(self, account_id: int) -> bool
```

**PositionService - 持仓服务**
```python
class PositionService:
    def __init__(self, repo: Repository):
        self.repo = repo

    def get_positions(self, account_id: int) -> list[Position]
    def calculate_position(self, account_id: int, symbol: str,
                          transactions: list[Transaction]) -> Position | None
    def get_account_summary(self, account_id: int) -> AccountSummary
    def get_holding_pnl(self, account_id: int, symbol: str) -> Decimal | None
```

**TransactionService - 交易服务**
```python
class TransactionService:
    def __init__(self, repo: Repository):
        self.repo = repo

    def add_transaction(self, transaction: Transaction) -> Transaction
    def get_transactions(self, account_id: int, limit: int = 100) -> list[Transaction]
    def buy_stock(self, account_id: int, symbol: str, shares: int,
                  price: Decimal, fee: Decimal = Decimal('0')) -> bool
    def sell_stock(self, account_id: int, symbol: str, shares: int,
                   price: Decimal, fee: Decimal = Decimal('0')) -> bool
    def get_transactions_by_symbol(self, account_id: int, symbol: str) -> list[Transaction]
```

### 3.2 量化选股服务 (`src/screening/`)

```
src/screening/
├── __init__.py
├── strategies.py    # 策略定义
└── screener.py      # 选股引擎
```

**StrategyRegistry - 策略注册表**
```python
class StrategyRegistry:
    """策略注册表，内置预设策略"""

    @staticmethod
    def get_all_strategies() -> list[Strategy]:
        return [
            Strategy(
                id="value",
                name="价值投资",
                description="低PE、低PB、高股息",
                category="价值",
                params={
                    "max_pe": 15,
                    "max_pb": 2,
                    "min_dividend_yield": 3,
                }
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
                }
            ),
            Strategy(
                id="low_pe",
                name="低估值",
                description="PE低于行业平均",
                category="价值",
                params={
                    "max_pe": 10,
                }
            ),
            Strategy(
                id="momentum",
                name="动量策略",
                description="股价突破均线、成交量放大",
                category="技术",
                params={
                    "ma_period": 20,
                    "volume_multiplier": 1.5,
                }
            ),
        ]

    @staticmethod
    def get_strategy(strategy_id: str) -> Strategy | None
```

**StockScreener - 选股引擎**
```python
class StockScreener:
    def __init__(self, repo: Repository):
        self.repo = repo
        self.fundamental_analyzer = FundamentalAnalyzer(repo)
        self.technical_analyzer = TechnicalAnalyzer(repo)

    def screen(self, strategy_id: str, params: dict,
               market: Market) -> list[ScreenResult]:
        """执行选股策略"""
        # 1. 获取股票池
        # 2. 应用筛选条件
        # 3. 计算匹配分数
        # 4. 返回排序结果

    def _screen_value_strategy(self, stocks: list[StockInfo],
                                params: dict) -> list[ScreenResult]
    def _screen_growth_strategy(self, stocks: list[StockInfo],
                                 params: dict) -> list[ScreenResult]
    def _screen_low_pe_strategy(self, stocks: list[StockInfo],
                                 params: dict) -> list[ScreenResult]
    def _screen_momentum_strategy(self, stocks: list[StockInfo],
                                   params: dict) -> list[ScreenResult]
```

---

## 四、Streamlit页面设计

### 4.1 组合管理页面

**文件**: `src/pages/6_💼_组合管理.py`

页面结构：
- 账户选择器（下拉选择 + 新建按钮）
- 账户概览卡片（总资产、现金、持仓市值、总盈亏）
- 持仓列表表格（股票、数量、成本、现价、盈亏、操作）
- 交易记录表格（日期、股票、类型、数量、价格、金额）
- 添加交易对话框

### 4.2 量化选股页面

**文件**: `src/pages/7_🔍_量化选股.py`

页面结构：
- 策略选择器（单选按钮组）
- 参数调整区域（根据策略动态显示）
- 开始筛选按钮
- 筛选结果表格（代码、名称、匹配度、关键指标、操作）
- 批量加入自选股功能

---

## 五、实现计划

实现将分两个阶段进行：

**阶段一：组合管理**
1. 数据库表结构创建
2. 数据模型定义
3. 业务逻辑层实现
4. Streamlit页面开发
5. 测试

**阶段二：量化选股**
1. 策略注册表实现
2. 选股引擎实现
3. Streamlit页面开发
4. 测试

---

## 六、依赖更新

无需新增外部依赖，使用现有技术栈。
