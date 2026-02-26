# 股票分析平台实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个支持A股、港股、美股的股票分析平台，提供基本面/技术面分析和AI辅助决策。

**Architecture:** 单体应用架构，Streamlit作为Web框架，MySQL存储数据，APScheduler处理定时任务，OpenAI GPT-5提供AI分析。

**Tech Stack:** Python 3.11+, Streamlit, MySQL 8.0, Tushare, Futu API, yfinance, OpenAI API, pandas-ta, APScheduler

---

## Phase 1: 基础设施

### Task 1: 初始化项目结构

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `docker-compose.yml`

**Step 1: 创建pyproject.toml**

```toml
[project]
name = "stock-analyzer"
version = "0.1.0"
description = "股票分析平台 - 支持A股、港股、美股"
requires-python = ">=3.11"
dependencies = [
    "streamlit>=1.30",
    "tushare>=1.4.0",
    "futu-api>=6.0.0",
    "yfinance>=0.2.0",
    "pandas>=2.0",
    "numpy>=1.24",
    "sqlalchemy>=2.0",
    "pymysql>=1.1",
    "pandas-ta>=0.3.14",
    "openai>=1.0",
    "plotly>=5.18",
    "apscheduler>=3.10",
    "python-dotenv>=1.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "loguru>=0.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP"]
```

**Step 2: 创建.env.example**

```
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=stock_analyzer

# 数据源配置
TUSHARE_TOKEN=your_tushare_token

# 富途配置
FUTU_HOST=127.0.0.1
FUTU_PORT=11111

# AI配置
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://your-proxy.com/v1
OPENAI_MODEL=gpt-5
```

**Step 3: 创建.gitignore**

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env
.env.local

# Streamlit
.streamlit/secrets.toml

# Logs
*.log
logs/

# Test
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
```

**Step 4: 创建docker-compose.yml**

```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    container_name: stock-mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD:-root123}
      MYSQL_DATABASE: stock_analyzer
      MYSQL_CHARSET: utf8mb4
      MYSQL_COLLATION: utf8mb4_unicode_ci
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci --default-authentication-plugin=mysql_native_password
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  mysql_data:
```

**Step 5: 同步依赖**

Run: `uv sync`
Expected: 创建 .venv 并安装依赖

**Step 6: 提交**

```bash
git add pyproject.toml .env.example .gitignore docker-compose.yml
git commit -m "chore: 初始化项目结构"
```

---

### Task 2: 创建目录结构和配置模块

**Files:**
- Create: `config/__init__.py`
- Create: `config/settings.py`
- Create: `src/__init__.py`
- Create: `src/models/__init__.py`
- Create: `src/data/__init__.py`
- Create: `src/analysis/__init__.py`
- Create: `src/ai/__init__.py`
- Create: `src/monitor/__init__.py`
- Create: `sql/init.sql`

**Step 1: 创建配置模块 config/settings.py**

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 数据库配置
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "stock_analyzer"

    # 数据源配置
    tushare_token: str = ""
    futu_host: str = "127.0.0.1"
    futu_port: int = 11111

    # AI配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 2: 创建数据库初始化脚本 sql/init.sql**

```sql
-- 股票基础信息表
CREATE TABLE IF NOT EXISTS stocks (
    symbol VARCHAR(20) PRIMARY KEY COMMENT '股票代码',
    name VARCHAR(100) COMMENT '股票名称',
    market ENUM('A股', '港股', '美股') COMMENT '市场',
    industry VARCHAR(50) COMMENT '所属行业',
    list_date DATE COMMENT '上市日期',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 日线行情表
CREATE TABLE IF NOT EXISTS daily_quotes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open DECIMAL(10,3) COMMENT '开盘价',
    high DECIMAL(10,3) COMMENT '最高价',
    low DECIMAL(10,3) COMMENT '最低价',
    close DECIMAL(10,3) COMMENT '收盘价',
    volume BIGINT COMMENT '成交量',
    amount DECIMAL(18,2) COMMENT '成交额',
    turnover_rate DECIMAL(5,2) COMMENT '换手率',
    pre_close DECIMAL(10,3) COMMENT '前收盘价',
    UNIQUE KEY uk_symbol_date (symbol, trade_date),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 财务数据表
CREATE TABLE IF NOT EXISTS financials (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    report_date DATE NOT NULL COMMENT '报告期',
    revenue DECIMAL(18,2) COMMENT '营业收入',
    net_profit DECIMAL(18,2) COMMENT '净利润',
    total_assets DECIMAL(18,2) COMMENT '总资产',
    total_equity DECIMAL(18,2) COMMENT '股东权益',
    roe DECIMAL(5,2) COMMENT '净资产收益率',
    pe DECIMAL(8,2) COMMENT '市盈率',
    pb DECIMAL(8,2) COMMENT '市净率',
    debt_ratio DECIMAL(5,2) COMMENT '资产负债率',
    gross_margin DECIMAL(5,2) COMMENT '毛利率',
    UNIQUE KEY uk_symbol_report (symbol, report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 自选股表
CREATE TABLE IF NOT EXISTS watchlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '添加时间',
    notes TEXT COMMENT '用户备注',
    alert_price_high DECIMAL(10,3) COMMENT '价格上限预警',
    alert_price_low DECIMAL(10,3) COMMENT '价格下限预警',
    UNIQUE KEY uk_symbol (symbol),
    FOREIGN KEY (symbol) REFERENCES stocks(symbol) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 预警记录表
CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    alert_type VARCHAR(50) NOT NULL COMMENT '预警类型',
    message TEXT NOT NULL COMMENT '预警消息',
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '触发时间',
    is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读',
    INDEX idx_triggered_at (triggered_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 数据同步日志表
CREATE TABLE IF NOT EXISTS data_sync_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_type VARCHAR(50) NOT NULL COMMENT '数据类型',
    market VARCHAR(20) NOT NULL COMMENT '市场',
    last_sync_date DATE COMMENT '最后同步日期',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_type_market (data_type, market)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Step 3: 创建空__init__.py文件**

创建以下空文件：
- `config/__init__.py`
- `src/__init__.py`
- `src/models/__init__.py`
- `src/data/__init__.py`
- `src/analysis/__init__.py`
- `src/ai/__init__.py`
- `src/monitor/__init__.py`

**Step 4: 提交**

```bash
git add config/ src/ sql/
git commit -m "chore: 创建目录结构和配置模块"
```

---

## Phase 2: 数据模型

### Task 3: 定义Pydantic数据模型

**Files:**
- Create: `src/models/schemas.py`
- Create: `tests/__init__.py`
- Create: `tests/test_models.py`

**Step 1: 写测试 tests/test_models.py**

```python
from datetime import date

from src.models.schemas import DailyQuote, Financial, StockInfo


def test_stock_info():
    info = StockInfo(symbol="000001.SZ", name="平安银行", market="A股")
    assert info.symbol == "000001.SZ"
    assert info.name == "平安银行"
    assert info.market == "A股"


def test_daily_quote():
    quote = DailyQuote(
        symbol="000001.SZ",
        trade_date=date(2024, 1, 15),
        open=10.5,
        high=10.8,
        low=10.3,
        close=10.6,
        volume=1000000,
    )
    assert quote.symbol == "000001.SZ"
    assert quote.close == 10.6


def test_financial():
    fin = Financial(
        symbol="000001.SZ",
        report_date=date(2024, 3, 31),
        revenue=1000000000,
        net_profit=100000000,
        roe=15.5,
        pe=8.2,
    )
    assert fin.roe == 15.5
```

**Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL - 模块不存在

**Step 3: 实现数据模型 src/models/schemas.py**

```python
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Market(str, Enum):
    A_STOCK = "A股"
    HK_STOCK = "港股"
    US_STOCK = "美股"


class StockInfo(BaseModel):
    """股票基础信息"""

    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: Market = Field(..., description="市场")
    industry: Optional[str] = Field(None, description="所属行业")
    list_date: Optional[date] = Field(None, description="上市日期")


class DailyQuote(BaseModel):
    """日线行情"""

    symbol: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    open: Optional[Decimal] = Field(None, description="开盘价")
    high: Optional[Decimal] = Field(None, description="最高价")
    low: Optional[Decimal] = Field(None, description="最低价")
    close: Optional[Decimal] = Field(None, description="收盘价")
    volume: Optional[int] = Field(None, description="成交量")
    amount: Optional[Decimal] = Field(None, description="成交额")
    turnover_rate: Optional[Decimal] = Field(None, description="换手率")
    pre_close: Optional[Decimal] = Field(None, description="前收盘价")

    @property
    def change_pct(self) -> Optional[Decimal]:
        """涨跌幅"""
        if self.close and self.pre_close and self.pre_close != 0:
            return (self.close - self.pre_close) / self.pre_close * 100
        return None


class Financial(BaseModel):
    """财务数据"""

    symbol: str = Field(..., description="股票代码")
    report_date: date = Field(..., description="报告期")
    revenue: Optional[Decimal] = Field(None, description="营业收入")
    net_profit: Optional[Decimal] = Field(None, description="净利润")
    total_assets: Optional[Decimal] = Field(None, description="总资产")
    total_equity: Optional[Decimal] = Field(None, description="股东权益")
    roe: Optional[Decimal] = Field(None, description="净资产收益率")
    pe: Optional[Decimal] = Field(None, description="市盈率")
    pb: Optional[Decimal] = Field(None, description="市净率")
    debt_ratio: Optional[Decimal] = Field(None, description="资产负债率")
    gross_margin: Optional[Decimal] = Field(None, description="毛利率")


class WatchlistItem(BaseModel):
    """自选股项"""

    symbol: str
    added_at: datetime
    notes: Optional[str] = None
    alert_price_high: Optional[Decimal] = None
    alert_price_low: Optional[Decimal] = None


class Alert(BaseModel):
    """预警记录"""

    id: Optional[int] = None
    symbol: str
    alert_type: str
    message: str
    triggered_at: datetime
    is_read: bool = False


class ValuationResult(BaseModel):
    """估值分析结果"""

    pe: Optional[Decimal] = None
    pb: Optional[Decimal] = None
    industry_avg_pe: Optional[Decimal] = None
    pe_percentile: Optional[float] = None
    is_undervalued: Optional[bool] = None


class ProfitabilityResult(BaseModel):
    """盈利能力结果"""

    roe_current: Optional[Decimal] = None
    roe_avg_3y: Optional[Decimal] = None
    roe_trend: Optional[str] = None
    gross_margin: Optional[Decimal] = None


class GrowthResult(BaseModel):
    """成长性结果"""

    revenue_yoy: Optional[Decimal] = None
    profit_yoy: Optional[Decimal] = None
    revenue_cagr_3y: Optional[Decimal] = None


class HealthResult(BaseModel):
    """财务健康结果"""

    debt_ratio: Optional[Decimal] = None
    debt_trend: Optional[str] = None


class FundamentalReport(BaseModel):
    """基本面分析报告"""

    symbol: str
    valuation: ValuationResult
    profitability: ProfitabilityResult
    growth: GrowthResult
    financial_health: HealthResult
    overall_score: int = Field(..., ge=0, le=100)


class MACDResult(BaseModel):
    """MACD指标"""

    dif: Decimal
    dea: Decimal
    macd: Decimal

    def is_golden_cross(self) -> bool:
        return self.dif > self.dea and self.macd > 0


class KDJResult(BaseModel):
    """KDJ指标"""

    k: Decimal
    d: Decimal
    j: Decimal


class Indicators(BaseModel):
    """技术指标集合"""

    ma5: Optional[Decimal] = None
    ma20: Optional[Decimal] = None
    ma60: Optional[Decimal] = None
    macd: Optional[MACDResult] = None
    rsi: Optional[Decimal] = None
    kdj: Optional[KDJResult] = None


class TrendResult(BaseModel):
    """趋势分析结果"""

    direction: str
    current_price: Decimal


class SupportResistance(BaseModel):
    """支撑压力位"""

    resistance_1: Decimal
    resistance_2: Optional[Decimal] = None
    support_1: Decimal
    support_2: Optional[Decimal] = None


class TechnicalReport(BaseModel):
    """技术面分析报告"""

    symbol: str
    trend: TrendResult
    indicators: Indicators
    support_resistance: SupportResistance
    patterns: list[str] = Field(default_factory=list)


class AIAnalysis(BaseModel):
    """AI分析结果"""

    symbol: str
    summary: str
    recommendation: Optional[str] = None
    risks: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)
```

**Step 4: 运行测试确认通过**

Run: `uv run pytest tests/test_models.py -v`
Expected: PASS

**Step 5: 提交**

```bash
git add src/models/schemas.py tests/
git commit -m "feat: 定义Pydantic数据模型"
```

---

## Phase 3: 数据获取层

### Task 4: 实现数据源基类和Repository

**Files:**
- Create: `src/data/base.py`
- Create: `src/data/repository.py`
- Create: `tests/test_repository.py`

**Step 1: 写测试 tests/test_repository.py**

```python
import pytest
from datetime import date

from src.models.schemas import StockInfo, DailyQuote, Market
from src.data.repository import Repository


@pytest.fixture
def repo():
    # 使用内存SQLite测试
    return Repository("sqlite:///:memory:")


def test_save_and_get_stock_info(repo):
    info = StockInfo(symbol="000001.SZ", name="平安银行", market=Market.A_STOCK)
    repo.save_stock_info(info)

    result = repo.get_stock_info("000001.SZ")
    assert result is not None
    assert result.name == "平安银行"


def test_save_and_get_quotes(repo):
    quotes = [
        DailyQuote(symbol="000001.SZ", trade_date=date(2024, 1, 15), close=10.5, volume=1000),
        DailyQuote(symbol="000001.SZ", trade_date=date(2024, 1, 16), close=10.6, volume=1100),
    ]
    repo.save_quotes(quotes)

    result = repo.get_quotes("000001.SZ", days=30)
    assert len(result) == 2
    assert result[-1].close == 10.6
```

**Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_repository.py -v`
Expected: FAIL - 模块不存在

**Step 3: 实现数据源基类 src/data/base.py**

```python
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from src.models.schemas import DailyQuote, Financial, StockInfo


class BaseProvider(ABC):
    """数据源基类"""

    @abstractmethod
    def get_daily_quotes(self, symbol: str, start: date, end: date) -> list[DailyQuote]:
        """获取日线行情"""
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """获取股票基础信息"""
        pass

    @abstractmethod
    def get_financials(self, symbol: str, years: int = 5) -> list[Financial]:
        """获取财务数据"""
        pass

    @abstractmethod
    def search_stocks(self, keyword: str) -> list[StockInfo]:
        """搜索股票"""
        pass
```

**Step 4: 实现Repository src/data/repository.py**

```python
from datetime import date, datetime, timedelta
from typing import Optional

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.models.schemas import DailyQuote, Financial, StockInfo, Market, WatchlistItem, Alert


class Repository:
    """数据仓库"""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self._ensure_tables()

    def _ensure_tables(self):
        """确保表存在（SQLite兼容）"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100),
                    market VARCHAR(10),
                    industry VARCHAR(50),
                    list_date DATE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS daily_quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(20),
                    trade_date DATE,
                    open DECIMAL(10,3),
                    high DECIMAL(10,3),
                    low DECIMAL(10,3),
                    close DECIMAL(10,3),
                    volume BIGINT,
                    amount DECIMAL(18,2),
                    turnover_rate DECIMAL(5,2),
                    pre_close DECIMAL(10,3),
                    UNIQUE(symbol, trade_date)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS financials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(20),
                    report_date DATE,
                    revenue DECIMAL(18,2),
                    net_profit DECIMAL(18,2),
                    total_assets DECIMAL(18,2),
                    total_equity DECIMAL(18,2),
                    roe DECIMAL(5,2),
                    pe DECIMAL(8,2),
                    pb DECIMAL(8,2),
                    debt_ratio DECIMAL(5,2),
                    gross_margin DECIMAL(5,2),
                    UNIQUE(symbol, report_date)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(20) UNIQUE,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    alert_price_high DECIMAL(10,3),
                    alert_price_low DECIMAL(10,3)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(20),
                    alert_type VARCHAR(50),
                    message TEXT,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS data_sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_type VARCHAR(50),
                    market VARCHAR(20),
                    last_sync_date DATE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(data_type, market)
                )
            """))
            conn.commit()

    def save_stock_info(self, info: StockInfo):
        """保存股票信息"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO stocks (symbol, name, market, industry, list_date)
                VALUES (:symbol, :name, :market, :industry, :list_date)
                ON DUPLICATE KEY UPDATE name=VALUES(name), industry=VALUES(industry)
            """), {
                "symbol": info.symbol,
                "name": info.name,
                "market": info.market.value if isinstance(info.market, Market) else info.market,
                "industry": info.industry,
                "list_date": info.list_date,
            })
            conn.commit()

    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """获取股票信息"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM stocks WHERE symbol = :symbol"), {"symbol": symbol})
            row = result.fetchone()
            if row:
                return StockInfo(
                    symbol=row[0],
                    name=row[1],
                    market=row[2],
                    industry=row[3],
                    list_date=row[4],
                )
        return None

    def save_quotes(self, quotes: list[DailyQuote]):
        """批量保存行情数据"""
        if not quotes:
            return
        with self.engine.connect() as conn:
            for q in quotes:
                conn.execute(text("""
                    INSERT INTO daily_quotes (symbol, trade_date, open, high, low, close, volume, amount, turnover_rate, pre_close)
                    VALUES (:symbol, :trade_date, :open, :high, :low, :close, :volume, :amount, :turnover_rate, :pre_close)
                    ON DUPLICATE KEY UPDATE close=VALUES(close), volume=VALUES(volume)
                """), {
                    "symbol": q.symbol,
                    "trade_date": q.trade_date,
                    "open": float(q.open) if q.open else None,
                    "high": float(q.high) if q.high else None,
                    "low": float(q.low) if q.low else None,
                    "close": float(q.close) if q.close else None,
                    "volume": q.volume,
                    "amount": float(q.amount) if q.amount else None,
                    "turnover_rate": float(q.turnover_rate) if q.turnover_rate else None,
                    "pre_close": float(q.pre_close) if q.pre_close else None,
                })
            conn.commit()
        logger.info(f"保存了 {len(quotes)} 条行情数据")

    def get_quotes(self, symbol: str, days: int = 365) -> list[DailyQuote]:
        """获取最近N天的行情"""
        start_date = date.today() - timedelta(days=days)
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT symbol, trade_date, open, high, low, close, volume, amount, turnover_rate, pre_close
                FROM daily_quotes
                WHERE symbol = :symbol AND trade_date >= :start_date
                ORDER BY trade_date ASC
            """), {"symbol": symbol, "start_date": start_date})
            quotes = []
            for row in result:
                from decimal import Decimal
                quotes.append(DailyQuote(
                    symbol=row[0],
                    trade_date=row[1],
                    open=Decimal(str(row[2])) if row[2] else None,
                    high=Decimal(str(row[3])) if row[3] else None,
                    low=Decimal(str(row[4])) if row[4] else None,
                    close=Decimal(str(row[5])) if row[5] else None,
                    volume=row[6],
                    amount=Decimal(str(row[7])) if row[7] else None,
                    turnover_rate=Decimal(str(row[8])) if row[8] else None,
                    pre_close=Decimal(str(row[9])) if row[9] else None,
                ))
        return quotes

    def get_latest_quote(self, symbol: str) -> Optional[DailyQuote]:
        """获取最新行情"""
        quotes = self.get_quotes(symbol, days=7)
        return quotes[-1] if quotes else None

    def save_financials(self, financials: list[Financial]):
        """批量保存财务数据"""
        if not financials:
            return
        with self.engine.connect() as conn:
            for f in financials:
                conn.execute(text("""
                    INSERT INTO financials (symbol, report_date, revenue, net_profit, total_assets, total_equity, roe, pe, pb, debt_ratio, gross_margin)
                    VALUES (:symbol, :report_date, :revenue, :net_profit, :total_assets, :total_equity, :roe, :pe, :pb, :debt_ratio, :gross_margin)
                    ON DUPLICATE KEY UPDATE roe=VALUES(roe), pe=VALUES(pe)
                """), {
                    "symbol": f.symbol,
                    "report_date": f.report_date,
                    "revenue": float(f.revenue) if f.revenue else None,
                    "net_profit": float(f.net_profit) if f.net_profit else None,
                    "total_assets": float(f.total_assets) if f.total_assets else None,
                    "total_equity": float(f.total_equity) if f.total_equity else None,
                    "roe": float(f.roe) if f.roe else None,
                    "pe": float(f.pe) if f.pe else None,
                    "pb": float(f.pb) if f.pb else None,
                    "debt_ratio": float(f.debt_ratio) if f.debt_ratio else None,
                    "gross_margin": float(f.gross_margin) if f.gross_margin else None,
                })
            conn.commit()

    def get_financials(self, symbol: str, years: int = 5) -> list[Financial]:
        """获取财务数据"""
        start_date = date.today() - timedelta(days=years * 365)
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM financials
                WHERE symbol = :symbol AND report_date >= :start_date
                ORDER BY report_date ASC
            """), {"symbol": symbol, "start_date": start_date})
            financials = []
            for row in result:
                from decimal import Decimal
                financials.append(Financial(
                    symbol=row[1],
                    report_date=row[2],
                    revenue=Decimal(str(row[3])) if row[3] else None,
                    net_profit=Decimal(str(row[4])) if row[4] else None,
                    total_assets=Decimal(str(row[5])) if row[5] else None,
                    total_equity=Decimal(str(row[6])) if row[6] else None,
                    roe=Decimal(str(row[7])) if row[7] else None,
                    pe=Decimal(str(row[8])) if row[8] else None,
                    pb=Decimal(str(row[9])) if row[9] else None,
                    debt_ratio=Decimal(str(row[10])) if row[10] else None,
                    gross_margin=Decimal(str(row[11])) if row[11] else None,
                ))
        return financials

    # 自选股操作
    def get_watchlist(self) -> list[WatchlistItem]:
        """获取自选股列表"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM watchlist ORDER BY added_at DESC"))
            items = []
            for row in result:
                from decimal import Decimal
                items.append(WatchlistItem(
                    symbol=row[1],
                    added_at=row[2],
                    notes=row[3],
                    alert_price_high=Decimal(str(row[4])) if row[4] else None,
                    alert_price_low=Decimal(str(row[5])) if row[5] else None,
                ))
        return items

    def add_to_watchlist(self, symbol: str, notes: str = None):
        """添加到自选股"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO watchlist (symbol, notes) VALUES (:symbol, :notes)
            """), {"symbol": symbol, "notes": notes})
            conn.commit()

    def remove_from_watchlist(self, symbol: str):
        """从自选股移除"""
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM watchlist WHERE symbol = :symbol"), {"symbol": symbol})
            conn.commit()

    # 预警操作
    def save_alert(self, alert: Alert):
        """保存预警记录"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO alerts (symbol, alert_type, message, triggered_at, is_read)
                VALUES (:symbol, :alert_type, :message, :triggered_at, :is_read)
            """), {
                "symbol": alert.symbol,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "triggered_at": alert.triggered_at,
                "is_read": alert.is_read,
            })
            conn.commit()

    def get_alerts(self, limit: int = 50) -> list[Alert]:
        """获取预警记录"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM alerts ORDER BY triggered_at DESC LIMIT :limit
            """), {"limit": limit})
            alerts = []
            for row in result:
                alerts.append(Alert(
                    id=row[0],
                    symbol=row[1],
                    alert_type=row[2],
                    message=row[3],
                    triggered_at=row[4],
                    is_read=bool(row[5]),
                ))
        return alerts

    def get_last_sync_date(self, data_type: str, market: str) -> Optional[date]:
        """获取最后同步日期"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT last_sync_date FROM data_sync_log
                WHERE data_type = :data_type AND market = :market
            """), {"data_type": data_type, "market": market})
            row = result.fetchone()
            return row[0] if row else None

    def update_sync_log(self, data_type: str, market: str, sync_date: date):
        """更新同步日志"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO data_sync_log (data_type, market, last_sync_date)
                VALUES (:data_type, :market, :sync_date)
                ON DUPLICATE KEY UPDATE last_sync_date = :sync_date
            """), {"data_type": data_type, "market": market, "sync_date": sync_date})
            conn.commit()
```

**Step 5: 运行测试确认通过**

Run: `uv run pytest tests/test_repository.py -v`
Expected: PASS

**Step 6: 提交**

```bash
git add src/data/base.py src/data/repository.py tests/test_repository.py
git commit -m "feat: 实现数据源基类和Repository"
```

---

### Task 5: 实现Tushare数据源（A股）

**Files:**
- Create: `src/data/tushare_provider.py`
- Create: `tests/test_tushare_provider.py`

**Step 1: 写测试 tests/test_tushare_provider.py**

```python
import pytest
from unittest.mock import Mock, patch
from datetime import date

from src.data.tushare_provider import TushareProvider
from src.models.schemas import DailyQuote, StockInfo, Market


@pytest.fixture
def provider():
    return TushareProvider("test_token")


def test_parse_symbol_a_stock(provider):
    """测试A股代码解析"""
    ts_code, market = provider._parse_symbol("000001.SZ")
    assert ts_code == "000001.SZ"
    assert market == Market.A_STOCK


def test_to_stock_info(provider):
    """测试转换为StockInfo"""
    row = {
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "industry": "银行",
    }
    info = provider._to_stock_info(row)
    assert info.symbol == "000001.SZ"
    assert info.name == "平安银行"
```

**Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_tushare_provider.py -v`
Expected: FAIL - 模块不存在

**Step 3: 实现Tushare数据源 src/data/tushare_provider.py**

```python
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
        """解析股票代码"""
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

    def get_daily_quotes(self, symbol: str, start: date, end: date) -> list[DailyQuote]:
        """获取日线行情"""
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
            quotes.append(DailyQuote(
                symbol=symbol,
                trade_date=date(int(str(row["trade_date"])[:4]), int(str(row["trade_date"])[4:6]), int(str(row["trade_date"])[6:8])),
                open=Decimal(str(row["open"])) if row["open"] else None,
                high=Decimal(str(row["high"])) if row["high"] else None,
                low=Decimal(str(row["low"])) if row["low"] else None,
                close=Decimal(str(row["close"])) if row["close"] else None,
                volume=int(row["vol"]) if row["vol"] else None,
                amount=Decimal(str(row["amount"])) * 1000 if row["amount"] else None,  # 千元转元
                pre_close=Decimal(str(row["pre_close"])) if row["pre_close"] else None,
            ))
        return quotes

    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """获取股票基础信息"""
        ts_code, market = self._parse_symbol(symbol)
        df = self.pro.stock_basic(ts_code=ts_code, fields="ts_code,symbol,name,area,industry,list_date")
        if df.empty:
            return None

        row = df.iloc[0]
        return StockInfo(
            symbol=symbol,
            name=row["name"],
            market=market,
            industry=row["industry"],
            list_date=date(int(str(row["list_date"])[:4]), int(str(row["list_date"])[4:6]), int(str(row["list_date"])[6:8])) if row["list_date"] else None,
        )

    def get_financials(self, symbol: str, years: int = 5) -> list[Financial]:
        """获取财务数据"""
        ts_code, _ = self._parse_symbol(symbol)
        start_date = (date.today() - timedelta(days=years * 365)).strftime("%Y%m%d")

        df = self.pro.fina_indicator(ts_code=ts_code, start_date=start_date, fields="ts_code,ann_date,roe,pe,pb,debt_to_assets,grossprofit_margin")

        financials = []
        for _, row in df.iterrows():
            if row["ann_date"]:
                financials.append(Financial(
                    symbol=symbol,
                    report_date=date(int(str(row["ann_date"])[:4]), int(str(row["ann_date"])[4:6]), int(str(row["ann_date"])[6:8])),
                    roe=Decimal(str(row["roe"])) if row["roe"] else None,
                    pe=Decimal(str(row["pe"])) if row["pe"] else None,
                    pb=Decimal(str(row["pb"])) if row["pb"] else None,
                    debt_ratio=Decimal(str(row["debt_to_assets"])) if row["debt_to_assets"] else None,
                    gross_margin=Decimal(str(row["grossprofit_margin"])) if row["grossprofit_margin"] else None,
                ))
        return financials

    def search_stocks(self, keyword: str) -> list[StockInfo]:
        """搜索股票"""
        df = self.pro.stock_basic(fields="ts_code,symbol,name,area,industry,list_date")
        df = df[df["name"].str.contains(keyword, na=False)]

        results = []
        for _, row in df.iterrows():
            results.append(StockInfo(
                symbol=row["ts_code"],
                name=row["name"],
                market=Market.A_STOCK,
                industry=row["industry"],
            ))
        return results
```

**Step 4: 运行测试确认通过**

Run: `uv run pytest tests/test_tushare_provider.py -v`
Expected: PASS

**Step 5: 提交**

```bash
git add src/data/tushare_provider.py tests/test_tushare_provider.py
git commit -m "feat: 实现Tushare数据源(A股)"
```

---

### Task 6: 实现YFinance数据源（美股）

**Files:**
- Create: `src/data/yfinance_provider.py`
- Create: `tests/test_yfinance_provider.py`

**Step 1: 写测试 tests/test_yfinance_provider.py**

```python
import pytest
from unittest.mock import Mock, patch
from datetime import date
from decimal import Decimal

from src.data.yfinance_provider import YFinanceProvider
from src.models.schemas import Market


@pytest.fixture
def provider():
    return YFinanceProvider()


def test_parse_symbol_us_stock(provider):
    """测试美股代码解析"""
    symbol, market = provider._parse_symbol("AAPL.US")
    assert symbol == "AAPL"
    assert market == Market.US_STOCK


def test_parse_symbol_without_suffix(provider):
    """测试无后缀代码"""
    symbol, market = provider._parse_symbol("TSLA")
    assert symbol == "TSLA"
    assert market == Market.US_STOCK
```

**Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_yfinance_provider.py -v`
Expected: FAIL - 模块不存在

**Step 3: 实现YFinance数据源 src/data/yfinance_provider.py**

```python
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
```

**Step 4: 运行测试确认通过**

Run: `uv run pytest tests/test_yfinance_provider.py -v`
Expected: PASS

**Step 5: 提交**

```bash
git add src/data/yfinance_provider.py tests/test_yfinance_provider.py
git commit -m "feat: 实现YFinance数据源(美股)"
```

---

### Task 7: 实现富途数据源（港股）

**Files:**
- Create: `src/data/futu_provider.py`
- Create: `tests/test_futu_provider.py`

**Step 1: 写测试 tests/test_futu_provider.py**

```python
import pytest
from src.data.futu_provider import FutuProvider
from src.models.schemas import Market


@pytest.fixture
def provider():
    # 实际使用时需要运行FutuOpenD
    return FutuProvider("127.0.0.1", 11111)


def test_parse_symbol_hk_stock(provider):
    """测试港股代码解析"""
    symbol, market = provider._parse_symbol("00700.HK")
    assert symbol == "HK.00700"
    assert market == Market.HK_STOCK


def test_parse_symbol_without_suffix(provider):
    """测试无后缀代码"""
    symbol, market = provider._parse_symbol("00700")
    assert symbol == "HK.00700"
    assert market == Market.HK_STOCK
```

**Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_futu_provider.py -v`
Expected: FAIL - 模块不存在

**Step 3: 实现富途数据源 src/data/futu_provider.py**

```python
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from futu import OpenQuoteContext, KLType, AuType
from loguru import logger

from src.data.base import BaseProvider
from src.models.schemas import DailyQuote, Financial, StockInfo, Market


class FutuProvider(BaseProvider):
    """富途数据源（港股）"""

    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        self.host = host
        self.port = port

    def _get_quote_ctx(self):
        """获取行情上下文"""
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
                turnover=Decimal(str(row["turnover"])),
            ))
        return quotes

    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
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
        # 这里返回空列表，实际使用时可补充
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
        return results[:20]  # 限制返回数量
```

**Step 4: 运行测试确认通过**

Run: `uv run pytest tests/test_futu_provider.py -v`
Expected: PASS

**Step 5: 提交**

```bash
git add src/data/futu_provider.py tests/test_futu_provider.py
git commit -m "feat: 实现富途数据源(港股)"
```

---

## Phase 4: 分析逻辑层

### Task 8: 实现技术指标计算

**Files:**
- Create: `src/analysis/indicators.py`
- Create: `tests/test_indicators.py`

**Step 1: 写测试 tests/test_indicators.py**

```python
import pytest
import pandas as pd
from decimal import Decimal

from src.analysis.indicators import calc_macd, calc_rsi, calc_kdj


@pytest.fixture
def sample_df():
    """创建测试数据"""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    closes = [100 + i * 0.5 + (-1) ** i * 2 for i in range(100)]
    df = pd.DataFrame({"close": closes, "high": [c + 2 for c in closes], "low": [c - 2 for c in closes]}, index=dates)
    return df


def test_calc_macd(sample_df):
    """测试MACD计算"""
    result = calc_macd(sample_df)
    assert result.dif is not None
    assert result.dea is not None
    assert result.macd is not None


def test_calc_rsi(sample_df):
    """测试RSI计算"""
    rsi = calc_rsi(sample_df)
    assert 0 <= rsi <= 100


def test_calc_kdj(sample_df):
    """测试KDJ计算"""
    result = calc_kdj(sample_df)
    assert result.k is not None
    assert result.d is not None
    assert result.j is not None
```

**Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_indicators.py -v`
Expected: FAIL - 模块不存在

**Step 3: 实现技术指标 src/analysis/indicators.py**

```python
from decimal import Decimal
import pandas as pd
import numpy as np

from src.models.schemas import MACDResult, KDJResult


def calc_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> MACDResult:
    """计算MACD指标"""
    closes = df["close"]
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = (dif - dea) * 2

    return MACDResult(
        dif=Decimal(str(dif.iloc[-1])),
        dea=Decimal(str(dea.iloc[-1])),
        macd=Decimal(str(macd.iloc[-1])),
    )


def calc_rsi(df: pd.DataFrame, period: int = 14) -> Decimal:
    """计算RSI指标"""
    closes = df["close"]
    delta = closes.diff()

    gain = delta.where(delta > 0, 0)
    loss = (-delta.where(delta < 0, 0)).abs()

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return Decimal(str(rsi.iloc[-1]))


def calc_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> KDJResult:
    """计算KDJ指标"""
    low_min = df["low"].rolling(window=n, min_periods=n).min()
    high_max = df["high"].rolling(window=n, min_periods=n).max()

    rsv = (df["close"] - low_min) / (high_max - low_min) * 100
    rsv = rsv.fillna(50)

    k = rsv.ewm(span=m1, adjust=False).mean()
    d = k.ewm(span=m2, adjust=False).mean()
    j = 3 * k - 2 * d

    return KDJResult(
        k=Decimal(str(k.iloc[-1])),
        d=Decimal(str(d.iloc[-1])),
        j=Decimal(str(j.iloc[-1])),
    )


def calc_ma(df: pd.DataFrame, periods: list[int] = [5, 10, 20, 60]) -> dict[int, Decimal]:
    """计算均线"""
    result = {}
    for period in periods:
        if len(df) >= period:
            ma = df["close"].rolling(window=period).mean().iloc[-1]
            result[period] = Decimal(str(ma))
    return result


def calc_bollinger(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> dict:
    """计算布林带"""
    closes = df["close"]
    middle = closes.rolling(window=period).mean()
    std = closes.rolling(window=period).std()

    return {
        "upper": Decimal(str((middle + std * std_dev).iloc[-1])),
        "middle": Decimal(str(middle.iloc[-1])),
        "lower": Decimal(str((middle - std * std_dev).iloc[-1])),
    }
```

**Step 4: 运行测试确认通过**

Run: `uv run pytest tests/test_indicators.py -v`
Expected: PASS

**Step 5: 提交**

```bash
git add src/analysis/indicators.py tests/test_indicators.py
git commit -m "feat: 实现技术指标计算"
```

---

### Task 9: 实现技术面分析器

**Files:**
- Create: `src/analysis/technical.py`
- Create: `tests/test_technical.py`

**Step 1: 写测试 tests/test_technical.py**

```python
import pytest
from unittest.mock import Mock
from datetime import date
from decimal import Decimal

from src.analysis.technical import TechnicalAnalyzer
from src.models.schemas import DailyQuote


@pytest.fixture
def mock_repo():
    repo = Mock()
    quotes = [
        DailyQuote(symbol="000001.SZ", trade_date=date(2024, 1, i), close=Decimal(str(10 + i * 0.1)), high=Decimal(str(10.5 + i * 0.1)), low=Decimal(str(9.5 + i * 0.1)), volume=1000000)
        for i in range(1, 100)
    ]
    repo.get_quotes.return_value = quotes
    return repo


def test_technical_analyzer(mock_repo):
    """测试技术分析器"""
    analyzer = TechnicalAnalyzer(mock_repo)
    report = analyzer.analyze("000001.SZ", days=90)

    assert report.symbol == "000001.SZ"
    assert report.trend is not None
    assert report.indicators is not None


def test_analyze_trend(mock_repo):
    """测试趋势分析"""
    analyzer = TechnicalAnalyzer(mock_repo)
    report = analyzer.analyze("000001.SZ", days=90)

    assert report.trend.direction in ["强势上涨", "震荡偏强", "震荡偏弱", "弱势下跌", "横盘整理"]
```

**Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_technical.py -v`
Expected: FAIL - 模块不存在

**Step 3: 实现技术面分析器 src/analysis/technical.py**

```python
from datetime import date
from decimal import Decimal
from typing import Optional

import pandas as pd
from loguru import logger

from src.data.repository import Repository
from src.models.schemas import DailyQuote, TechnicalReport, TrendResult, Indicators, SupportResistance
from src.analysis.indicators import calc_macd, calc_rsi, calc_kdj, calc_ma, calc_bollinger


class TechnicalAnalyzer:
    """技术面分析器"""

    def __init__(self, repo: Repository):
        self.repo = repo

    def analyze(self, symbol: str, days: int = 365) -> TechnicalReport:
        """生成技术面分析报告"""
        quotes = self.repo.get_quotes(symbol, days)
        if not quotes:
            raise ValueError(f"未找到股票数据: {symbol}")

        df = self._to_dataframe(quotes)

        return TechnicalReport(
            symbol=symbol,
            trend=self._analyze_trend(df),
            indicators=self._calc_indicators(df),
            support_resistance=self._find_support_resistance(df),
            patterns=self._detect_patterns(df),
        )

    def _to_dataframe(self, quotes: list[DailyQuote]) -> pd.DataFrame:
        """转换为DataFrame"""
        data = {
            "date": [q.trade_date for q in quotes],
            "open": [float(q.open) if q.open else None for q in quotes],
            "high": [float(q.high) if q.high else None for q in quotes],
            "low": [float(q.low) if q.low else None for q in quotes],
            "close": [float(q.close) if q.close else None for q in quotes],
            "volume": [q.volume for q in quotes],
        }
        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        return df

    def _analyze_trend(self, df: pd.DataFrame) -> TrendResult:
        """趋势分析"""
        closes = df["close"]
        current_price = Decimal(str(closes.iloc[-1]))

        ma20 = closes.rolling(20).mean().iloc[-1]
        ma60 = closes.rolling(60).mean().iloc[-1] if len(df) >= 60 else ma20

        # 判断趋势
        if current_price > Decimal(str(ma20)) > Decimal(str(ma60)):
            direction = "强势上涨"
        elif current_price > Decimal(str(ma20)):
            direction = "震荡偏强"
        elif current_price < Decimal(str(ma20)) < Decimal(str(ma60)):
            direction = "弱势下跌"
        elif current_price < Decimal(str(ma20)):
            direction = "震荡偏弱"
        else:
            direction = "横盘整理"

        return TrendResult(direction=direction, current_price=current_price)

    def _calc_indicators(self, df: pd.DataFrame) -> Indicators:
        """计算技术指标"""
        ma_dict = calc_ma(df, [5, 20, 60])

        return Indicators(
            ma5=ma_dict.get(5),
            ma20=ma_dict.get(20),
            ma60=ma_dict.get(60),
            macd=calc_macd(df) if len(df) >= 26 else None,
            rsi=calc_rsi(df) if len(df) >= 14 else None,
            kdj=calc_kdj(df) if len(df) >= 9 else None,
        )

    def _find_support_resistance(self, df: pd.DataFrame) -> SupportResistance:
        """识别支撑压力位"""
        recent = df.tail(60) if len(df) >= 60 else df

        highs = recent["high"].dropna()
        lows = recent["low"].dropna()

        # 找局部极值
        resistance_1 = Decimal(str(highs.nlargest(3).iloc[0])) if len(highs) >= 3 else Decimal(str(highs.max()))
        resistance_2 = Decimal(str(highs.nlargest(3).iloc[1])) if len(highs) >= 3 else None
        support_1 = Decimal(str(lows.nsmallest(3).iloc[0])) if len(lows) >= 3 else Decimal(str(lows.min()))
        support_2 = Decimal(str(lows.nsmallest(3).iloc[1])) if len(lows) >= 3 else None

        return SupportResistance(
            resistance_1=resistance_1,
            resistance_2=resistance_2,
            support_1=support_1,
            support_2=support_2,
        )

    def _detect_patterns(self, df: pd.DataFrame) -> list[str]:
        """K线形态识别"""
        patterns = []
        if len(df) < 3:
            return patterns

        # 简单形态识别
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 大阳线
        if last["close"] > last["open"] * 1.03:
            patterns.append("大阳线")

        # 大阴线
        if last["close"] < last["open"] * 0.97:
            patterns.append("大阴线")

        # 十字星
        if abs(last["close"] - last["open"]) / last["open"] < 0.01:
            patterns.append("十字星")

        return patterns
```

**Step 4: 运行测试确认通过**

Run: `uv run pytest tests/test_technical.py -v`
Expected: PASS

**Step 5: 提交**

```bash
git add src/analysis/technical.py tests/test_technical.py
git commit -m "feat: 实现技术面分析器"
```

---

### Task 10: 实现基本面分析器

**Files:**
- Create: `src/analysis/fundamental.py`
- Create: `tests/test_fundamental.py`

**Step 1: 写测试 tests/test_fundamental.py**

```python
import pytest
from unittest.mock import Mock
from datetime import date
from decimal import Decimal

from src.analysis.fundamental import FundamentalAnalyzer
from src.models.schemas import Financial


@pytest.fixture
def mock_repo():
    repo = Mock()
    financials = [
        Financial(symbol="000001.SZ", report_date=date(2024, 3, 31), roe=Decimal("15.5"), pe=Decimal("8.2"), gross_margin=Decimal("40.0"), debt_ratio=Decimal("35.0")),
        Financial(symbol="000001.SZ", report_date=date(2023, 12, 31), roe=Decimal("14.8"), pe=Decimal("7.5"), gross_margin=Decimal("38.5"), debt_ratio=Decimal("36.0")),
        Financial(symbol="000001.SZ", report_date=date(2023, 9, 30), roe=Decimal("14.2"), pe=Decimal("7.0"), gross_margin=Decimal("37.0"), debt_ratio=Decimal("37.0")),
    ]
    repo.get_financials.return_value = financials
    return repo


def test_fundamental_analyzer(mock_repo):
    """测试基本面分析器"""
    analyzer = FundamentalAnalyzer(mock_repo)
    report = analyzer.analyze("000001.SZ", years=3)

    assert report.symbol == "000001.SZ"
    assert 0 <= report.overall_score <= 100


def test_valuation_analysis(mock_repo):
    """测试估值分析"""
    analyzer = FundamentalAnalyzer(mock_repo)
    report = analyzer.analyze("000001.SZ", years=3)

    assert report.valuation.pe is not None
```

**Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_fundamental.py -v`
Expected: FAIL - 模块不存在

**Step 3: 实现基本面分析器 src/analysis/fundamental.py**

```python
import statistics
from datetime import date
from decimal import Decimal
from typing import Optional

from loguru import logger

from src.data.repository import Repository
from src.models.schemas import (
    Financial,
    FundamentalReport,
    ValuationResult,
    ProfitabilityResult,
    GrowthResult,
    HealthResult,
)


class FundamentalAnalyzer:
    """基本面分析器"""

    def __init__(self, repo: Repository):
        self.repo = repo

    def analyze(self, symbol: str, years: int = 5) -> FundamentalReport:
        """生成基本面分析报告"""
        financials = self.repo.get_financials(symbol, years)
        if not financials:
            raise ValueError(f"未找到财务数据: {symbol}")

        return FundamentalReport(
            symbol=symbol,
            valuation=self._analyze_valuation(financials),
            profitability=self._analyze_profitability(financials),
            growth=self._analyze_growth(financials),
            financial_health=self._analyze_health(financials),
            overall_score=self._calculate_score(financials),
        )

    def _analyze_valuation(self, financials: list[Financial]) -> ValuationResult:
        """估值分析"""
        latest = financials[-1]
        pe = latest.pe
        pb = latest.pb

        # 简单判断是否低估（PE < 15）
        is_undervalued = pe is not None and pe < Decimal("15")

        return ValuationResult(
            pe=pe,
            pb=pb,
            is_undervalued=is_undervalued,
        )

    def _analyze_profitability(self, financials: list[Financial]) -> ProfitabilityResult:
        """盈利能力分析"""
        roe_values = [f.roe for f in financials if f.roe is not None]
        gross_margins = [f.gross_margin for f in financials if f.gross_margin is not None]

        roe_current = roe_values[-1] if roe_values else None
        roe_avg_3y = Decimal(str(statistics.mean(roe_values[-4:]))) if len(roe_values) >= 4 else roe_current

        # 判断ROE趋势
        roe_trend = "稳定"
        if len(roe_values) >= 2:
            if roe_values[-1] > roe_values[-2]:
                roe_trend = "上升"
            elif roe_values[-1] < roe_values[-2]:
                roe_trend = "下降"

        return ProfitabilityResult(
            roe_current=roe_current,
            roe_avg_3y=roe_avg_3y,
            roe_trend=roe_trend,
            gross_margin=gross_margins[-1] if gross_margins else None,
        )

    def _analyze_growth(self, financials: list[Financial]) -> GrowthResult:
        """成长性分析"""
        revenues = [f.revenue for f in financials if f.revenue is not None]
        profits = [f.net_profit for f in financials if f.net_profit is not None]

        revenue_yoy = None
        profit_yoy = None

        if len(revenues) >= 2 and revenues[-2] and revenues[-2] != 0:
            revenue_yoy = (revenues[-1] - revenues[-2]) / revenues[-2] * 100

        if len(profits) >= 2 and profits[-2] and profits[-2] != 0:
            profit_yoy = (profits[-1] - profits[-2]) / profits[-2] * 100

        return GrowthResult(
            revenue_yoy=revenue_yoy,
            profit_yoy=profit_yoy,
        )

    def _analyze_health(self, financials: list[Financial]) -> HealthResult:
        """财务健康分析"""
        debt_ratios = [f.debt_ratio for f in financials if f.debt_ratio is not None]

        current_debt = debt_ratios[-1] if debt_ratios else None
        debt_trend = "稳定"

        if len(debt_ratios) >= 2:
            if debt_ratios[-1] < debt_ratios[-2]:
                debt_trend = "改善"
            elif debt_ratios[-1] > debt_ratios[-2]:
                debt_trend = "恶化"

        return HealthResult(
            debt_ratio=current_debt,
            debt_trend=debt_trend,
        )

    def _calculate_score(self, financials: list[Financial]) -> int:
        """计算综合评分 (0-100)"""
        score = 50  # 基础分

        latest = financials[-1]

        # ROE评分 (+/-20分)
        if latest.roe:
            if latest.roe > 20:
                score += 20
            elif latest.roe > 15:
                score += 15
            elif latest.roe > 10:
                score += 10
            elif latest.roe < 5:
                score -= 10

        # PE评分 (+/-15分)
        if latest.pe:
            if latest.pe < 10:
                score += 15
            elif latest.pe < 15:
                score += 10
            elif latest.pe < 20:
                score += 5
            elif latest.pe > 50:
                score -= 10

        # 负债率评分 (+/-10分)
        if latest.debt_ratio:
            if latest.debt_ratio < 30:
                score += 10
            elif latest.debt_ratio < 50:
                score += 5
            elif latest.debt_ratio > 70:
                score -= 10

        # 毛利率评分 (+/-5分)
        if latest.gross_margin:
            if latest.gross_margin > 40:
                score += 5
            elif latest.gross_margin < 20:
                score -= 5

        return max(0, min(100, score))
```

**Step 4: 运行测试确认通过**

Run: `uv run pytest tests/test_fundamental.py -v`
Expected: PASS

**Step 5: 提交**

```bash
git add src/analysis/fundamental.py tests/test_fundamental.py
git commit -m "feat: 实现基本面分析器"
```

---

## Phase 5: AI服务层

### Task 11: 实现OpenAI客户端

**Files:**
- Create: `src/ai/client.py`
- Create: `src/ai/prompts.py`
- Create: `tests/test_ai_client.py`

**Step 1: 写测试 tests/test_ai_client.py**

```python
import pytest
from unittest.mock import Mock, patch

from src.ai.client import AIClient


@pytest.fixture
def client():
    return AIClient(api_key="test_key", base_url="https://api.openai.com/v1", model="gpt-4")


def test_client_initialization(client):
    """测试客户端初始化"""
    assert client.model == "gpt-4"


@patch("src.ai.client.OpenAI")
def test_analyze_stock(mock_openai, client):
    """测试股票分析"""
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="这是一条分析结果"))]
    client.client.chat.completions.create.return_value = mock_response

    result = client.analyze_stock("000001.SZ", {}, {})
    assert result.summary == "这是一条分析结果"
```

**Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_ai_client.py -v`
Expected: FAIL - 模块不存在

**Step 3: 实现OpenAI客户端 src/ai/client.py**

```python
from datetime import datetime
from typing import Optional

from openai import OpenAI
from loguru import logger

from src.models.schemas import AIAnalysis


class AIClient:
    """OpenAI客户端"""

    def __init__(self, api_key: str, base_url: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def analyze_stock(
        self,
        symbol: str,
        fundamental: dict,
        technical: dict,
    ) -> AIAnalysis:
        """综合分析股票"""
        from src.ai.prompts import Prompts

        prompt = Prompts.stock_analysis(symbol, fundamental, technical)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": Prompts.SYSTEM_ANALYST},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            content = response.choices[0].message.content
            return AIAnalysis(
                symbol=symbol,
                summary=content,
                generated_at=datetime.now(),
            )
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return AIAnalysis(
                symbol=symbol,
                summary=f"分析失败: {str(e)}",
                generated_at=datetime.now(),
            )

    def chat(self, messages: list[dict], user_message: str) -> str:
        """对话式问答"""
        all_messages = messages + [{"role": "user", "content": user_message}]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=all_messages,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"对话失败: {e}")
            return f"抱歉，我遇到了一些问题: {str(e)}"

    def compare_stocks(self, stocks_data: list[dict]) -> str:
        """对比分析多只股票"""
        from src.ai.prompts import Prompts

        prompt = Prompts.compare_stocks(stocks_data)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": Prompts.SYSTEM_ANALYST},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"对比分析失败: {e}")
            return f"分析失败: {str(e)}"
```

**Step 4: 实现提示词模板 src/ai/prompts.py**

```python
class Prompts:
    """提示词模板"""

    SYSTEM_ANALYST = """你是一位专业的股票分析师，擅长基本面和技术面分析。
你的分析应该：
1. 客观中立，基于数据说话
2. 指出风险点和机会点
3. 给出明确的操作建议（买入/持有/卖出）及理由
4. 使用中文回复，语言简洁专业
5. 避免过于绝对的表达，投资有风险"""

    @staticmethod
    def stock_analysis(symbol: str, fundamental: dict, technical: dict) -> str:
        """生成股票分析提示词"""
        fund_text = "\n".join([f"- {k}: {v}" for k, v in fundamental.items()]) if fundamental else "暂无基本面数据"
        tech_text = "\n".join([f"- {k}: {v}" for k, v in technical.items()]) if technical else "暂无技术面数据"

        return f"""请分析以下股票并给出投资建议：

【股票代码】{symbol}

【基本面数据】
{fund_text}

【技术面数据】
{tech_text}

请给出：
1. 综合评价（2-3句话）
2. 投资建议（买入/持有/卖出）及理由
3. 风险提示
4. 建议关注的关键点位或指标"""

    @staticmethod
    def compare_stocks(stocks_data: list[dict]) -> str:
        """生成对比分析提示词"""
        stocks_text = ""
        for i, data in enumerate(stocks_data, 1):
            stocks_text += f"\n--- 股票{i} ---\n"
            stocks_text += f"代码: {data.get('symbol', 'N/A')}\n"
            stocks_text += f"名称: {data.get('name', 'N/A')}\n"
            stocks_text += f"PE: {data.get('pe', 'N/A')}\n"
            stocks_text += f"ROE: {data.get('roe', 'N/A')}\n"
            stocks_text += f"趋势: {data.get('trend', 'N/A')}\n"

        return f"""请对比分析以下股票，帮助用户选择：

{stocks_text}

请从估值、成长性、技术形态等角度对比，给出优先推荐顺序和理由。"""
```

**Step 5: 运行测试确认通过**

Run: `uv run pytest tests/test_ai_client.py -v`
Expected: PASS

**Step 6: 提交**

```bash
git add src/ai/client.py src/ai/prompts.py tests/test_ai_client.py
git commit -m "feat: 实现AI服务层"
```

---

## Phase 6: Streamlit页面

### Task 12: 创建Streamlit主入口

**Files:**
- Create: `src/app.py`

**Step 1: 实现主入口 src/app.py**

```python
import streamlit as st
from config.settings import get_settings
from src.data.repository import Repository

# 页面配置
st.set_page_config(
    page_title="股票分析平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化
@st.cache_resource
def get_repo():
    settings = get_settings()
    return Repository(settings.database_url)


def main():
    st.title("📈 股票分析平台")
    st.markdown("支持A股、港股、美股的基本面和技术面分析")

    # 概览
    repo = get_repo()
    watchlist = repo.get_watchlist()
    alerts = repo.get_alerts(limit=10)
    unread_alerts = [a for a in alerts if not a.is_read]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("自选股数量", len(watchlist))
    with col2:
        st.metric("未读预警", len(unread_alerts))
    with col3:
        st.metric("支持市场", "A股/港股/美股")

    st.markdown("---")

    # 快速搜索
    st.subheader("快速搜索")
    symbol = st.text_input(
        "输入股票代码",
        placeholder="如：000001.SZ, 00700.HK, AAPL.US",
        key="quick_search",
    )

    if symbol:
        st.session_state["analyze_symbol"] = symbol
        st.info(f"已选择: {symbol}，请前往「基本面」或「技术分析」页面查看详情")

    # 最近预警
    if unread_alerts:
        st.subheader("最近预警")
        for alert in unread_alerts[:5]:
            with st.container(border=True):
                st.markdown(f"**{alert.symbol}** - {alert.alert_type}")
                st.caption(alert.message)


if __name__ == "__main__":
    main()
```

**Step 2: 验证应用可启动**

Run: `uv run streamlit run src/app.py --server.headless true`
Expected: 应用启动无报错

**Step 3: 提交**

```bash
git add src/app.py
git commit -m "feat: 创建Streamlit主入口"
```

---

### Task 13: 创建自选股页面

**Files:**
- Create: `src/pages/1_📊_自选股.py`

**Step 1: 实现自选股页面**

```python
import streamlit as st
from decimal import Decimal

from config.settings import get_settings
from src.data.repository import Repository
from src.data.tushare_provider import TushareProvider
from src.data.yfinance_provider import YFinanceProvider

st.set_page_config(page_title="自选股", page_icon="📊", layout="wide")

settings = get_settings()
repo = Repository(settings.database_url)


def get_provider(symbol: str):
    """根据代码获取数据源"""
    if symbol.endswith(".SZ") or symbol.endswith(".SH") or symbol.endswith(".BJ"):
        return TushareProvider(settings.tushare_token)
    else:
        return YFinanceProvider()


st.title("📊 自选股")

# 添加自选股
with st.expander("➕ 添加自选股"):
    col1, col2 = st.columns([3, 1])
    with col1:
        new_symbol = st.text_input("股票代码", placeholder="如：000001.SZ, AAPL.US")
    with col2:
        if st.button("添加", type="primary"):
            if new_symbol:
                try:
                    repo.add_to_watchlist(new_symbol)
                    st.success(f"已添加 {new_symbol}")
                    st.rerun()
                except Exception as e:
                    st.error(f"添加失败: {e}")

# 自选股列表
st.subheader("我的自选股")
watchlist = repo.get_watchlist()

if not watchlist:
    st.info("暂无自选股，请添加")
else:
    for item in watchlist:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

            info = repo.get_stock_info(item.symbol)
            latest = repo.get_latest_quote(item.symbol)

            with col1:
                name = info.name if info else item.symbol
                st.markdown(f"**{name}**")
                st.caption(item.symbol)

            with col2:
                if latest:
                    change = latest.change_pct
                    st.metric(
                        "现价",
                        f"{latest.close:.2f}" if latest.close else "-",
                        f"{change:+.2f}%" if change else None,
                        delta_color="normal" if change and change > 0 else "inverse",
                    )
                else:
                    st.metric("现价", "-")

            with col3:
                if item.alert_price_high or item.alert_price_low:
                    st.caption(f"预警: {item.alert_price_low or '-'} ~ {item.alert_price_high or '-'}")

            with col4:
                if st.button("分析", key=f"analyze_{item.symbol}"):
                    st.session_state["analyze_symbol"] = item.symbol
                    st.switch_page("pages/3_📄_基本面.py")

                if st.button("删除", key=f"delete_{item.symbol}"):
                    repo.remove_from_watchlist(item.symbol)
                    st.rerun()
```

**Step 2: 提交**

```bash
git add src/pages/1_📊_自选股.py
git commit -m "feat: 创建自选股页面"
```

---

### Task 14: 创建技术分析页面

**Files:**
- Create: `src/pages/2_📈_技术分析.py`

**Step 1: 实现技术分析页面**

```python
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta

from config.settings import get_settings
from src.data.repository import Repository
from src.analysis.technical import TechnicalAnalyzer

st.set_page_config(page_title="技术分析", page_icon="📈", layout="wide")

settings = get_settings()
repo = Repository(settings.database_url)

st.title("📈 技术分析")

# 股票选择
default_symbol = st.session_state.get("analyze_symbol", "")
symbol = st.text_input("股票代码", value=default_symbol, placeholder="如：000001.SZ")

if symbol:
    # 时间范围
    period_map = {"3个月": 90, "6个月": 180, "1年": 365, "3年": 1095}
    period_label = st.select_slider("时间范围", options=list(period_map.keys()), value="1年")
    days = period_map[period_label]

    try:
        analyzer = TechnicalAnalyzer(repo)
        report = analyzer.analyze(symbol, days=days)

        # K线图
        quotes = repo.get_quotes(symbol, days)

        col1, col2 = st.columns([3, 1])

        with col1:
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
            )

            # K线
            fig.add_trace(
                go.Candlestick(
                    x=[q.trade_date for q in quotes],
                    open=[float(q.open) for q in quotes],
                    high=[float(q.high) for q in quotes],
                    low=[float(q.low) for q in quotes],
                    close=[float(q.close) for q in quotes],
                    name="K线",
                ),
                row=1,
                col=1,
            )

            # 成交量
            fig.add_trace(
                go.Bar(
                    x=[q.trade_date for q in quotes],
                    y=[q.volume for q in quotes],
                    name="成交量",
                    marker_color="lightblue",
                ),
                row=2,
                col=1,
            )

            fig.update_layout(
                title=f"{symbol} K线图",
                xaxis_rangeslider_visible=False,
                height=600,
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # 趋势判断
            st.subheader("趋势分析")
            trend = report.trend
            if "上涨" in trend.direction:
                st.success(f"**{trend.direction}**")
            elif "下跌" in trend.direction:
                st.error(f"**{trend.direction}**")
            else:
                st.info(f"**{trend.direction}**")

            st.metric("当前价", f"{trend.current_price:.2f}")

            # 支撑压力
            st.subheader("支撑/压力")
            sr = report.support_resistance
            st.write(f"🔺 压力1: {sr.resistance_1:.2f}")
            if sr.resistance_2:
                st.write(f"🔺 压力2: {sr.resistance_2:.2f}")
            st.write(f"🔻 支撑1: {sr.support_1:.2f}")
            if sr.support_2:
                st.write(f"🔻 支撑2: {sr.support_2:.2f}")

        # 技术指标
        st.subheader("技术指标")
        ind = report.indicators

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("MA5", f"{ind.ma5:.2f}" if ind.ma5 else "-")
            st.metric("MA20", f"{ind.ma20:.2f}" if ind.ma20 else "-")
            st.metric("MA60", f"{ind.ma60:.2f}" if ind.ma60 else "-")

        with col2:
            if ind.macd:
                st.metric("MACD", f"{ind.macd.macd:.3f}")
                st.metric("DIF", f"{ind.macd.dif:.3f}")
                st.metric("DEA", f"{ind.macd.dea:.3f}")

        with col3:
            if ind.rsi:
                rsi = ind.rsi
                color = "red" if rsi > 70 else "green" if rsi < 30 else "gray"
                st.metric("RSI(14)", f"{rsi:.1f}")
                if rsi > 70:
                    st.caption("⚠️ 超买")
                elif rsi < 30:
                    st.caption("⚠️ 超卖")

        with col4:
            if ind.kdj:
                st.metric("K", f"{ind.kdj.k:.1f}")
                st.metric("D", f"{ind.kdj.d:.1f}")
                st.metric("J", f"{ind.kdj.j:.1f}")

        # K线形态
        if report.patterns:
            st.subheader("K线形态")
            for pattern in report.patterns:
                st.markdown(f"- {pattern}")

    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"分析失败: {e}")
```

**Step 2: 提交**

```bash
git add src/pages/2_📈_技术分析.py
git commit -m "feat: 创建技术分析页面"
```

---

### Task 15: 创建基本面页面

**Files:**
- Create: `src/pages/3_📄_基本面.py`

**Step 1: 实现基本面页面**

```python
import streamlit as st
import plotly.graph_objects as go

from config.settings import get_settings
from src.data.repository import Repository
from src.analysis.fundamental import FundamentalAnalyzer

st.set_page_config(page_title="基本面分析", page_icon="📄", layout="wide")

settings = get_settings()
repo = Repository(settings.database_url)

st.title("📄 基本面分析")

# 股票选择
default_symbol = st.session_state.get("analyze_symbol", "")
symbol = st.text_input("股票代码", value=default_symbol, placeholder="如：000001.SZ")

if symbol:
    try:
        analyzer = FundamentalAnalyzer(repo)
        report = analyzer.analyze(symbol, years=5)

        # 综合评分
        col1, col2 = st.columns([1, 3])

        with col1:
            score = report.overall_score
            st.metric("综合评分", f"{score}/100")

            if score >= 80:
                st.success("优秀 ⭐")
            elif score >= 60:
                st.info("良好 👍")
            else:
                st.warning("一般 ⚠️")

        with col2:
            # 评分雷达图
            categories = ["估值", "盈利", "成长", "健康"]
            values = [
                100 if report.valuation.is_undervalued else 50,
                min(100, float(report.profitability.roe_current or 0) * 4),
                50,  # 简化处理
                100 - float(report.financial_health.debt_ratio or 50),
            ]

            fig = go.Figure(
                data=go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                )
            )
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)

        # 详细分析
        tab1, tab2, tab3, tab4 = st.tabs(["估值分析", "盈利能力", "成长性", "财务健康"])

        with tab1:
            val = report.valuation
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("PE(市盈率)", f"{val.pe:.1f}" if val.pe else "-")
            with col2:
                st.metric("PB(市净率)", f"{val.pb:.2f}" if val.pb else "-")
            with col3:
                status = "低估 ✅" if val.is_undervalued else "合理/高估"
                st.metric("估值判断", status)

        with tab2:
            prof = report.profitability
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ROE(净资产收益率)", f"{prof.roe_current:.1f}%" if prof.roe_current else "-")
            with col2:
                st.metric("ROE 3年均值", f"{prof.roe_avg_3y:.1f}%" if prof.roe_avg_3y else "-")
            with col3:
                st.metric("ROE趋势", prof.roe_trend or "-")

            st.metric("毛利率", f"{prof.gross_margin:.1f}%" if prof.gross_margin else "-")

        with tab3:
            growth = report.growth
            col1, col2 = st.columns(2)
            with col1:
                if growth.revenue_yoy:
                    st.metric("营收同比增长", f"{growth.revenue_yoy:.1f}%")
            with col2:
                if growth.profit_yoy:
                    st.metric("利润同比增长", f"{growth.profit_yoy:.1f}%")

        with tab4:
            health = report.financial_health
            col1, col2 = st.columns(2)
            with col1:
                st.metric("资产负债率", f"{health.debt_ratio:.1f}%" if health.debt_ratio else "-")
            with col2:
                st.metric("趋势", health.debt_trend or "-")

    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"分析失败: {e}")
```

**Step 2: 提交**

```bash
git add src/pages/3_📄_基本面.py
git commit -m "feat: 创建基本面分析页面"
```

---

### Task 16: 创建监控预警页面

**Files:**
- Create: `src/pages/4_🔔_监控预警.py`

**Step 1: 实现监控预警页面**

```python
import streamlit as st
from decimal import Decimal

from config.settings import get_settings
from src.data.repository import Repository

st.set_page_config(page_title="监控预警", page_icon="🔔", layout="wide")

settings = get_settings()
repo = Repository(settings.database_url)

st.title("🔔 监控预警")

tab1, tab2 = st.tabs(["预警设置", "预警记录"])

with tab1:
    st.subheader("自选股预警设置")
    watchlist = repo.get_watchlist()

    if not watchlist:
        st.info("请先添加自选股")
    else:
        for item in watchlist:
            with st.expander(f"📌 {item.symbol}"):
                col1, col2 = st.columns(2)
                with col1:
                    high = st.number_input(
                        "价格上限",
                        value=float(item.alert_price_high) if item.alert_price_high else 0.0,
                        key=f"high_{item.symbol}",
                    )
                with col2:
                    low = st.number_input(
                        "价格下限",
                        value=float(item.alert_price_low) if item.alert_price_low else 0.0,
                        key=f"low_{item.symbol}",
                    )

                if st.button("保存设置", key=f"save_{item.symbol}"):
                    # 更新预警设置
                    try:
                        with repo.engine.connect() as conn:
                            from sqlalchemy import text
                            conn.execute(
                                text("""
                                    UPDATE watchlist
                                    SET alert_price_high = :high, alert_price_low = :low
                                    WHERE symbol = :symbol
                                """),
                                {"high": high if high > 0 else None, "low": low if low > 0 else None, "symbol": item.symbol},
                            )
                            conn.commit()
                        st.success("已保存")
                    except Exception as e:
                        st.error(f"保存失败: {e}")

with tab2:
    st.subheader("历史预警")
    alerts = repo.get_alerts(limit=50)

    if not alerts:
        st.info("暂无预警记录")
    else:
        for alert in alerts:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    st.markdown(f"**{alert.symbol}**")
                    if alert.alert_type == "价格突破上限":
                        st.caption(f"🔴 {alert.alert_type}")
                    elif alert.alert_type == "价格跌破下限":
                        st.caption(f"🟢 {alert.alert_type}")
                    else:
                        st.caption(f"🟡 {alert.alert_type}")
                with col2:
                    st.write(alert.message)
                with col3:
                    st.caption(alert.triggered_at.strftime("%m-%d %H:%M"))

        # 标记全部已读
        if st.button("全部标为已读"):
            with repo.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("UPDATE alerts SET is_read = TRUE"))
                conn.commit()
            st.success("已全部标为已读")
            st.rerun()
```

**Step 2: 提交**

```bash
git add src/pages/4_🔔_监控预警.py
git commit -m "feat: 创建监控预警页面"
```

---

### Task 17: 创建AI助手页面

**Files:**
- Create: `src/pages/5_💬_AI助手.py`

**Step 1: 实现AI助手页面**

```python
import streamlit as st

from config.settings import get_settings
from src.data.repository import Repository
from src.ai.client import AIClient

st.set_page_config(page_title="AI助手", page_icon="💬", layout="wide")

settings = get_settings()
repo = Repository(settings.database_url)
ai_client = AIClient(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    model=settings.openai_model,
)

st.title("💬 AI投资助手")

# 初始化对话历史
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 显示对话历史
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 快捷问题
st.subheader("快捷问题")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("分析我的自选股"):
        st.session_state["pending_question"] = "请分析我的自选股，给出综合评价和推荐顺序"

with col2:
    if st.button("今日市场机会"):
        st.session_state["pending_question"] = "基于我的自选股，今天有哪些值得关注的交易机会？"

with col3:
    if st.button("风险评估"):
        st.session_state["pending_question"] = "评估我自选股的整体风险，给出建议"

# 输入框
if "pending_question" in st.session_state:
    prompt = st.session_state.pop("pending_question")
else:
    prompt = st.chat_input("输入你的问题...")

if prompt:
    # 显示用户消息
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 获取AI回复
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            # 构建上下文
            watchlist = repo.get_watchlist()
            context = f"用户当前有 {len(watchlist)} 只自选股: " + ", ".join([w.symbol for w in watchlist])

            # 添加上下文到对话
            messages_for_api = [
                {"role": "system", "content": f"你是专业的股票分析师。{context}"},
            ] + st.session_state.chat_history

            try:
                response = ai_client.chat(messages_for_api[:-1], prompt)
                st.write(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"AI回复失败: {e}")

# 清除对话
if st.button("清除对话"):
    st.session_state.chat_history = []
    st.rerun()
```

**Step 2: 提交**

```bash
git add src/pages/5_💬_AI助手.py
git commit -m "feat: 创建AI助手页面"
```

---

## Phase 7: 监控预警

### Task 18: 实现定时任务调度器

**Files:**
- Create: `src/monitor/scheduler.py`

**Step 1: 实现调度器 src/monitor/scheduler.py**

```python
from datetime import date, datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from config.settings import get_settings
from src.data.repository import Repository
from src.data.tushare_provider import TushareProvider
from src.data.yfinance_provider import YFinanceProvider
from src.monitor.alerts import AlertEngine


class DataScheduler:
    """数据同步调度器"""

    def __init__(self):
        self.settings = get_settings()
        self.repo = Repository(self.settings.database_url)
        self.scheduler = BackgroundScheduler()

        # 初始化数据源
        self.providers = {
            "A股": TushareProvider(self.settings.tushare_token),
            "美股": YFinanceProvider(),
        }

    def start(self):
        """启动调度器"""
        # 每15分钟更新自选股实时行情
        self.scheduler.add_job(
            self.update_watchlist_quotes,
            trigger=IntervalTrigger(minutes=15),
            id="update_quotes",
            replace_existing=True,
        )

        # 每日16:00同步历史数据
        self.scheduler.add_job(
            self.sync_daily_data,
            trigger=CronTrigger(hour=16, minute=0),
            id="sync_daily",
            replace_existing=True,
        )

        # 每15分钟检查预警条件
        self.scheduler.add_job(
            self.check_alerts,
            trigger=IntervalTrigger(minutes=15),
            id="check_alerts",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("调度器已启动")

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("调度器已停止")

    def update_watchlist_quotes(self):
        """更新自选股实时行情"""
        logger.info("开始更新自选股行情")
        watchlist = self.repo.get_watchlist()

        for item in watchlist:
            try:
                provider = self._get_provider(item.symbol)
                if provider:
                    quotes = provider.get_daily_quotes(
                        item.symbol,
                        date.today(),
                        date.today(),
                    )
                    if quotes:
                        self.repo.save_quotes(quotes)
                        logger.debug(f"更新 {item.symbol} 行情成功")
            except Exception as e:
                logger.error(f"更新 {item.symbol} 行情失败: {e}")

        logger.info("自选股行情更新完成")

    def sync_daily_data(self):
        """同步日线数据"""
        logger.info("开始同步日线数据")
        watchlist = self.repo.get_watchlist()

        for item in watchlist:
            try:
                provider = self._get_provider(item.symbol)
                if provider:
                    # 获取最后同步日期
                    last_date = self.repo.get_last_sync_date("daily_quote", self._get_market(item.symbol))
                    start_date = last_date or date.today().replace(year=date.today().year - 1)

                    quotes = provider.get_daily_quotes(item.symbol, start_date, date.today())
                    if quotes:
                        self.repo.save_quotes(quotes)
                        self.repo.update_sync_log("daily_quote", self._get_market(item.symbol), date.today())
            except Exception as e:
                logger.error(f"同步 {item.symbol} 数据失败: {e}")

        logger.info("日线数据同步完成")

    def check_alerts(self):
        """检查预警条件"""
        logger.info("开始检查预警条件")
        engine = AlertEngine(self.repo)
        engine.check_all()
        logger.info("预警检查完成")

    def _get_provider(self, symbol: str):
        """根据代码获取数据源"""
        if symbol.endswith((".SZ", ".SH", ".BJ")):
            return self.providers.get("A股")
        else:
            return self.providers.get("美股")

    def _get_market(self, symbol: str) -> str:
        """获取市场"""
        if symbol.endswith((".SZ", ".SH", ".BJ")):
            return "A股"
        elif symbol.endswith(".HK"):
            return "港股"
        else:
            return "美股"
```

**Step 2: 提交**

```bash
git add src/monitor/scheduler.py
git commit -m "feat: 实现定时任务调度器"
```

---

### Task 19: 实现预警引擎

**Files:**
- Create: `src/monitor/alerts.py`

**Step 1: 实现预警引擎 src/monitor/alerts.py**

```python
from datetime import datetime
from decimal import Decimal
from loguru import logger

from src.data.repository import Repository
from src.analysis.technical import TechnicalAnalyzer
from src.models.schemas import Alert


class AlertEngine:
    """预警引擎"""

    def __init__(self, repo: Repository):
        self.repo = repo

    def check_all(self):
        """检查所有预警条件"""
        watchlist = self.repo.get_watchlist()

        for item in watchlist:
            try:
                alerts = self._check_stock(item.symbol, item.alert_price_high, item.alert_price_low)
                for alert in alerts:
                    self.repo.save_alert(alert)
                    logger.info(f"触发预警: {alert.symbol} - {alert.alert_type}")
            except Exception as e:
                logger.error(f"检查 {item.symbol} 预警失败: {e}")

    def _check_stock(self, symbol: str, price_high: Decimal = None, price_low: Decimal = None) -> list[Alert]:
        """检查单只股票的预警条件"""
        alerts = []
        now = datetime.now()

        latest = self.repo.get_latest_quote(symbol)
        if not latest:
            return alerts

        # 1. 价格突破预警
        if price_high and latest.close and latest.close >= price_high:
            alerts.append(Alert(
                symbol=symbol,
                alert_type="价格突破上限",
                message=f"{symbol} 触及价格上限 {price_high}，当前价 {latest.close}",
                triggered_at=now,
            ))

        if price_low and latest.close and latest.close <= price_low:
            alerts.append(Alert(
                symbol=symbol,
                alert_type="价格跌破下限",
                message=f"{symbol} 跌破价格下限 {price_low}，当前价 {latest.close}",
                triggered_at=now,
            ))

        # 2. 异常波动预警
        if latest.change_pct:
            change = abs(latest.change_pct)
            if change >= 5:
                direction = "大涨" if latest.change_pct > 0 else "大跌"
                alerts.append(Alert(
                    symbol=symbol,
                    alert_type="异常波动",
                    message=f"{symbol} {direction} {change:.2f}%",
                    triggered_at=now,
                ))

        # 3. 技术指标预警
        try:
            analyzer = TechnicalAnalyzer(self.repo)
            report = analyzer.analyze(symbol, days=60)

            # MACD金叉
            if report.indicators.macd and report.indicators.macd.is_golden_cross():
                alerts.append(Alert(
                    symbol=symbol,
                    alert_type="MACD金叉",
                    message=f"{symbol} MACD出现金叉信号，可能上涨",
                    triggered_at=now,
                ))

            # RSI超买超卖
            if report.indicators.rsi:
                rsi = report.indicators.rsi
                if rsi > 80:
                    alerts.append(Alert(
                        symbol=symbol,
                        alert_type="RSI超买",
                        message=f"{symbol} RSI={rsi:.1f}，超买警惕回调",
                        triggered_at=now,
                    ))
                elif rsi < 20:
                    alerts.append(Alert(
                        symbol=symbol,
                        alert_type="RSI超卖",
                        message=f"{symbol} RSI={rsi:.1f}，超卖可能反弹",
                        triggered_at=now,
                    ))
        except Exception as e:
            logger.warning(f"技术指标预警检查失败 {symbol}: {e}")

        return alerts
```

**Step 2: 提交**

```bash
git add src/monitor/alerts.py
git commit -m "feat: 实现预警引擎"
```

---

### Task 20: 最终整合与测试

**Step 1: 运行所有测试**

Run: `uv run pytest tests/ -v`
Expected: 所有测试通过

**Step 2: 启动MySQL容器**

Run: `docker-compose up -d`
Expected: MySQL容器启动成功

**Step 3: 复制环境配置**

Run: `cp .env.example .env`
Expected: 创建.env文件

**Step 4: 编辑.env填入真实配置**

手动编辑.env文件，填入：
- TUSHARE_TOKEN
- OPENAI_API_KEY
- OPENAI_BASE_URL
- DB_PASSWORD

**Step 5: 启动应用**

Run: `uv run streamlit run src/app.py`
Expected: 应用在 http://localhost:8501 启动

**Step 6: 最终提交**

```bash
git add .
git commit -m "feat: 股票分析平台开发完成"
```

---

## 完成清单

- [ ] Task 1: 初始化项目结构
- [ ] Task 2: 创建目录结构和配置模块
- [ ] Task 3: 定义Pydantic数据模型
- [ ] Task 4: 实现数据源基类和Repository
- [ ] Task 5: 实现Tushare数据源（A股）
- [ ] Task 6: 实现YFinance数据源（美股）
- [ ] Task 7: 实现富途数据源（港股）
- [ ] Task 8: 实现技术指标计算
- [ ] Task 9: 实现技术面分析器
- [ ] Task 10: 实现基本面分析器
- [ ] Task 11: 实现OpenAI客户端
- [ ] Task 12: 创建Streamlit主入口
- [ ] Task 13: 创建自选股页面
- [ ] Task 14: 创建技术分析页面
- [ ] Task 15: 创建基本面页面
- [ ] Task 16: 创建监控预警页面
- [ ] Task 17: 创建AI助手页面
- [ ] Task 18: 实现定时任务调度器
- [ ] Task 19: 实现预警引擎
- [ ] Task 20: 最终整合与测试
