# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

一个支持A股、港股和美股的股票分析平台。使用 Python 和 Streamlit 构建，具备基本面分析、技术分析、AI 洞察和实时监控预警功能。

## 开发命令

```bash
# 安装依赖（需要 uv）
uv sync

# 运行 Streamlit 应用
uv run streamlit run src/app.py

# 运行测试
uv run pytest

# 运行测试并生成覆盖率报告
uv run pytest --cov

# 代码检查
uv run ruff check .

# 代码格式化
uv run ruff format .
```

## 数据库设置

应用使用 MySQL 8.0。使用 Docker 启动数据库：

```bash
docker-compose up -d
```

数据库会从 `sql/init.sql` 自动初始化。重置数据库：

```bash
docker-compose down -v  # 删除数据卷
docker-compose up -d    # 全新启动
```

## 架构设计

### 分层架构

```
Streamlit 页面 (src/pages/)
    ↓
分析层 (src/analysis/) - FundamentalAnalyzer, TechnicalAnalyzer
    ↓
数据服务层 (src/data/) - 市场数据的 Provider 模式
    ↓
数据仓库 (src/data/repository.py) - 基于 SQLAlchemy 的数据库访问
    ↓
MySQL 数据库
```

### 核心设计模式

**Provider 模式** (`src/data/base.py`)：抽象 `BaseProvider` 定义所有市场数据源的接口。实现类：
- `TushareProvider` - A股，通过 Tushare Pro API
- `FutuProvider` - 港股，通过 Futu OpenD
- `YFinanceProvider` - 美股，通过 yfinance

**Repository 模式** (`src/data/repository.py`)：使用 SQLAlchemy 的集中式数据库访问。所有数据库操作都通过此类进行。

**Settings 模式** (`config/settings.py`)：基于 Pydantic 的配置，支持通过 `.env` 文件设置环境变量。

### 目录结构

| 目录 | 用途 |
|-----------|---------|
| `src/pages/` | Streamlit 多页面应用 |
| `src/data/` | 数据提供者和仓库 |
| `src/analysis/` | 基本面和技术分析逻辑 |
| `src/ai/` | OpenAI 客户端和提示词 |
| `src/monitor/` | 基于 APScheduler 的预警和数据同步 |
| `src/models/` | Pydantic 数据模型 |
| `config/` | 应用配置 |
| `sql/` | 数据库初始化脚本 |

## 环境配置

复制 `.env.example` 为 `.env` 并配置：

- **数据库**: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- **数据源**: `TUSHARE_TOKEN`（A股必需）
- **富途**: `FUTU_HOST`, `FUTU_PORT`（需要运行 Futu OpenD 客户端）
- **AI**: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`

## 重要说明

- 如果 MySQL 不可用，应用默认使用 SQLite (`stock_analyzer.db`) 进行测试
- FutuProvider 需要本地运行 Futu OpenD 客户端
- 股票代码使用市场特定格式：`000001.SZ`（A股）、`00700.HK`（港股）、`AAPL`（美股）
- `src/models/schemas.py` 中的 `Market` 枚举定义了三个支持的市场
- 每日数据同步在 16:00 运行，预警检查每 15 分钟执行一次（配置在 `src/monitor/scheduler.py`）
