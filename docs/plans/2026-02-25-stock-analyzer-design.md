# 股票分析平台设计文档

## 项目概述

构建一个面向个人投资者的股票分析平台，支持A股、港股、美股三大市场的数据分析和AI辅助决策。

## 需求总结

| 项目 | 选择 |
|------|------|
| 目标用户 | 个人投资者 |
| 使用方式 | Web应用 |
| 技术栈 | Python全栈 + Streamlit |
| 部署方式 | 本地运行 + uv |
| 数据库 | MySQL (Docker) |
| AI服务 | OpenAI GPT-5 (中转) |
| 监控频率 | 准实时 (5-15分钟) |

**功能优先级：** 基本面 > 技术面 > 监控预警 > 组合管理 > 量化选股

---

## 架构设计

采用单体应用架构：

```
┌────────────────────────────────────────────────────────┐
│                    Streamlit Web                        │
│   首页 │ 自选股 │ 技术分析 │ 基本面 │ 监控 │ AI助手    │
├────────────────────────────────────────────────────────┤
│                      业务逻辑层                         │
│   FundamentalAnalyzer │ TechnicalAnalyzer │ AlertEngine│
├────────────────────────────────────────────────────────┤
│                      数据服务层                         │
│   Tushare(A股) │ Futu(港股) │ YFinance(美股) │ Repo    │
├────────────────────────────────────────────────────────┤
│   MySQL (Docker)     │     APScheduler (定时任务)      │
├────────────────────────────────────────────────────────┤
│                    AI服务 (OpenAI GPT-5)               │
└────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
stock-analyzer/
├── pyproject.toml          # uv项目配置
├── .env.example            # 环境变量模板
├── docker-compose.yml      # MySQL容器配置
│
├── config/
│   └── settings.py         # 配置管理（API密钥、数据库连接等）
│
├── src/
│   ├── app.py              # Streamlit主入口
│   │
│   ├── pages/              # Streamlit多页面
│   │   ├── 1_📊_自选股.py
│   │   ├── 2_📈_技术分析.py
│   │   ├── 3_📄_基本面.py
│   │   ├── 4_🔔_监控预警.py
│   │   └── 5_💬_AI助手.py
│   │
│   ├── data/               # 数据获取层
│   │   ├── base.py         # 数据源基类
│   │   ├── tushare_provider.py   # A股
│   │   ├── futu_provider.py      # 港股
│   │   ├── yfinance_provider.py  # 美股
│   │   └── repository.py   # 数据库操作
│   │
│   ├── analysis/           # 分析逻辑层
│   │   ├── fundamental.py  # 基本面分析
│   │   ├── technical.py    # 技术面分析
│   │   └── indicators.py   # 指标计算
│   │
│   ├── ai/                 # AI服务层
│   │   ├── client.py       # OpenAI客户端封装
│   │   └── prompts.py      # 提示词模板
│   │
│   ├── monitor/            # 监控预警
│   │   ├── scheduler.py    # 定时任务
│   │   └── alerts.py       # 预警规则
│   │
│   └── models/             # 数据模型
│       └── schemas.py      # Pydantic模型
│
└── sql/
    └── init.sql            # 数据库初始化脚本
```

---

## 数据模型

### 股票基础信息表
```sql
CREATE TABLE stocks (
    symbol VARCHAR(20) PRIMARY KEY,    -- 股票代码，如 000001.SZ, 00700.HK, AAPL.US
    name VARCHAR(100),                  -- 股票名称
    market ENUM('A股', '港股', '美股'),
    industry VARCHAR(50),               -- 所属行业
    list_date DATE,                     -- 上市日期
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 日线行情表
```sql
CREATE TABLE daily_quotes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20),
    trade_date DATE,
    open DECIMAL(10,3),
    high DECIMAL(10,3),
    low DECIMAL(10,3),
    close DECIMAL(10,3),
    volume BIGINT,
    amount DECIMAL(18,2),               -- 成交额
    turnover_rate DECIMAL(5,2),         -- 换手率
    UNIQUE KEY uk_symbol_date (symbol, trade_date)
);
```

### 财务数据表
```sql
CREATE TABLE financials (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20),
    report_date DATE,                   -- 报告期
    revenue DECIMAL(18,2),              -- 营业收入
    net_profit DECIMAL(18,2),           -- 净利润
    total_assets DECIMAL(18,2),         -- 总资产
    total_equity DECIMAL(18,2),         -- 股东权益
    roe DECIMAL(5,2),                   -- 净资产收益率
    pe DECIMAL(8,2),                    -- 市盈率
    pb DECIMAL(8,2),                    -- 市净率
    debt_ratio DECIMAL(5,2),            -- 资产负债率
    gross_margin DECIMAL(5,2),          -- 毛利率
    UNIQUE KEY uk_symbol_report (symbol, report_date)
);
```

### 自选股表
```sql
CREATE TABLE watchlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,                         -- 用户备注
    alert_price_high DECIMAL(10,3),     -- 价格上限预警
    alert_price_low DECIMAL(10,3),      -- 价格下限预警
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
);
```

### 预警记录表
```sql
CREATE TABLE alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20),
    alert_type VARCHAR(50),             -- 预警类型
    message TEXT,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE
);
```

### 数据同步日志表
```sql
CREATE TABLE data_sync_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_type VARCHAR(50),              -- daily_quote, financial 等
    market VARCHAR(20),
    last_sync_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 核心模块设计

### 数据获取层

采用Provider模式，统一不同市场的数据源接口：

```python
class BaseProvider(ABC):
    @abstractmethod
    def get_daily_quotes(self, symbol: str, start: date, end: date) -> list[DailyQuote]:
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> StockInfo:
        pass

    @abstractmethod
    def get_financials(self, symbol: str) -> list[Financial]:
        pass
```

**数据源配置：**
- A股：Tushare Pro API
- 港股：富途OpenD（需本地运行客户端）
- 美股：yfinance（免费，无需API Key）

### 分析逻辑层

#### 基本面分析
- 估值分析：PE/PB相对行业位置
- 盈利能力：ROE趋势、毛利率稳定性
- 成长性：营收/利润同比增长、CAGR
- 财务健康：资产负债率趋势
- 综合评分：0-100分

#### 技术面分析
- 趋势判断：均线系统（MA5/20/60）
- 技术指标：MACD、RSI、KDJ、布林带
- 支撑压力位：局部极值识别
- K线形态：常见形态识别

### AI服务层

```python
class AIClient:
    def analyze_stock(self, symbol, fundamental, technical) -> AIAnalysis:
        # 综合基本面和技术面数据，调用GPT-5生成分析报告

    def chat(self, history, user_message) -> str:
        # 对话式问答
```

**AI功能场景：**
1. 个股深度分析
2. 多股对比推荐
3. 自由问答
4. 风险解读

### 监控预警

**定时任务：**
- 每15分钟更新自选股实时行情
- 每日收盘后同步历史数据
- 每15分钟检查预警条件

**预警类型：**
| 类型 | 触发条件 | 级别 |
|------|----------|------|
| 价格突破 | 触及设定价格上下限 | 高 |
| 异常波动 | 涨跌幅≥5% | 中 |
| 成交量放大 | 量>20日均量2倍 | 中 |
| MACD金叉/死叉 | 技术信号 | 低 |
| RSI超买超卖 | RSI>80或<20 | 低 |
| 自定义规则 | 用户设置条件 | 用户定义 |

---

## Streamlit页面设计

| 页面 | 核心功能 |
|------|----------|
| 首页 | 概览、快速搜索 |
| 自选股 | 管理列表、快速查看行情 |
| 技术分析 | K线图、指标、趋势判断 |
| 基本面 | 估值、盈利、成长、健康度 |
| 监控预警 | 设置规则、查看历史 |
| AI助手 | 对话式分析、智能问答 |

---

## 技术栈

```toml
[project]
dependencies = [
    # Web框架
    "streamlit>=1.30",

    # 数据获取
    "tushare>=1.4.0",           # A股
    "futu-api>=6.0.0",          # 港股
    "yfinance>=0.2.0",          # 美股

    # 数据处理
    "pandas>=2.0",
    "numpy>=1.24",
    "sqlalchemy>=2.0",
    "pymysql>=1.1",

    # 技术分析
    "pandas-ta>=0.3.14",

    # AI
    "openai>=1.0",

    # 可视化
    "plotly>=5.18",

    # 定时任务
    "apscheduler>=3.10",

    # 配置管理
    "python-dotenv>=1.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",

    # 日志
    "loguru>=0.7",
]
```

**部署配置：**
- 数据库：MySQL 8.0 (Docker)
- 环境管理：uv

---

## 开发顺序

1. **基础设施**：Docker MySQL + 项目骨架
2. **数据层**：Tushare/YFinance/Futu接入 + 数据库存储
3. **分析层**：基本面分析 → 技术面分析
4. **页面开发**：自选股 → 基本面页 → 技术分析页
5. **AI集成**：分析报告生成 → 对话助手
6. **监控预警**：定时任务 → 预警规则

---

## 环境配置

```bash
# .env.example
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
