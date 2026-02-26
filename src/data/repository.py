"""
数据访问层Repository
负责与数据库交互，支持MySQL（生产）和SQLite（测试）
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.models.schemas import (
    Alert,
    AlertType,
    DailyQuote,
    Financial,
    Market,
    StockInfo,
    WatchlistItem,
)


class Repository:
    """数据访问层，封装所有数据库操作"""

    def __init__(self, db_url: str):
        """初始化Repository

        Args:
            db_url: 数据库连接URL，如 mysql+pymysql://user:pass@host/db 或 sqlite:///path/to/db.sqlite
        """
        self.engine: Engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        # 启用SQLite外键约束
        if "sqlite" in db_url:
            from sqlalchemy import event
            from sqlite3 import Connection

            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                if isinstance(dbapi_conn, Connection):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON;")
                    cursor.close()

        self._create_tables()
        logger.info(f"Repository initialized with {db_url}")

    def _create_tables(self):
        """创建数据库表（如果不存在）"""
        create_tables_sql = """
        -- 股票基础信息表
        CREATE TABLE IF NOT EXISTS stock_info (
            symbol VARCHAR(20) PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            market VARCHAR(20) NOT NULL,
            industry VARCHAR(50),
            list_date DATE
        );

        -- 日线行情表
        CREATE TABLE IF NOT EXISTS daily_quote (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(20) NOT NULL,
            trade_date DATE NOT NULL,
            open DECIMAL(12,4) NOT NULL,
            high DECIMAL(12,4) NOT NULL,
            low DECIMAL(12,4) NOT NULL,
            close DECIMAL(12,4) NOT NULL,
            volume BIGINT NOT NULL,
            pre_close DECIMAL(12,4),
            amount DECIMAL(18,4),
            turnover_rate DECIMAL(8,4),
            UNIQUE(symbol, trade_date)
        );

        -- 财务数据表
        CREATE TABLE IF NOT EXISTS financial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(20) NOT NULL,
            report_date DATE NOT NULL,
            revenue DECIMAL(18,4),
            net_profit DECIMAL(18,4),
            total_assets DECIMAL(18,4),
            total_equity DECIMAL(18,4),
            roe DECIMAL(8,4),
            pe DECIMAL(8,4),
            pb DECIMAL(8,4),
            debt_ratio DECIMAL(8,4),
            gross_margin DECIMAL(8,4),
            UNIQUE(symbol, report_date)
        );

        -- 自选股表
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol VARCHAR(20) PRIMARY KEY,
            added_at DATETIME NOT NULL,
            notes TEXT,
            alert_price_high DECIMAL(12,4),
            alert_price_low DECIMAL(12,4)
        );

        -- 预警记录表
        CREATE TABLE IF NOT EXISTS alert (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(20) NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            triggered_at DATETIME NOT NULL,
            is_read BOOLEAN DEFAULT FALSE
        );

        -- 数据同步日志表
        CREATE TABLE IF NOT EXISTS data_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_type VARCHAR(50) NOT NULL,
            market VARCHAR(20) NOT NULL,
            last_sync_date DATE NOT NULL,
            updated_at DATETIME NOT NULL,
            UNIQUE(data_type, market)
        );

        -- 账户表
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL,
            account_type VARCHAR(20) DEFAULT '证券账户',
            initial_capital DECIMAL(18,2) NOT NULL,
            current_cash DECIMAL(18,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 交易记录表
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
        );

        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_quote_symbol ON daily_quote(symbol);
        CREATE INDEX IF NOT EXISTS idx_quote_date ON daily_quote(trade_date);
        CREATE INDEX IF NOT EXISTS idx_financial_symbol ON financial(symbol);
        CREATE INDEX IF NOT EXISTS idx_alert_symbol ON alert(symbol);
        CREATE INDEX IF NOT EXISTS idx_alert_time ON alert(triggered_at);
        CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_symbol ON transactions(symbol);
        """

        with self.engine.connect() as conn:
            # 分割并执行每条SQL语句
            for statement in create_tables_sql.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))
            conn.commit()
        logger.debug("Database tables created/verified")

    # ============== StockInfo 操作 ==============

    def save_stock_info(self, info: StockInfo):
        """保存股票基础信息"""
        sql = """
        INSERT INTO stock_info (symbol, name, market, industry, list_date)
        VALUES (:symbol, :name, :market, :industry, :list_date)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            market = VALUES(market),
            industry = VALUES(industry),
            list_date = VALUES(list_date)
        """
        # SQLite使用INSERT OR REPLACE
        sqlite_sql = """
        INSERT OR REPLACE INTO stock_info (symbol, name, market, industry, list_date)
        VALUES (:symbol, :name, :market, :industry, :list_date)
        """

        params = {
            "symbol": info.symbol,
            "name": info.name,
            "market": info.market.value,
            "industry": info.industry,
            "list_date": info.list_date,
        }

        with self.engine.connect() as conn:
            try:
                conn.execute(text(sql), params)
            except Exception:
                # 如果MySQL语法失败，尝试SQLite语法
                conn.execute(text(sqlite_sql), params)
            conn.commit()
        logger.debug(f"Saved stock info: {info.symbol}")

    def get_stock_info(self, symbol: str) -> StockInfo | None:
        """获取股票基础信息"""
        sql = "SELECT * FROM stock_info WHERE symbol = :symbol"

        with self.engine.connect() as conn:
            result = conn.execute(text(sql), {"symbol": symbol}).fetchone()

        if result:
            return StockInfo(
                symbol=result.symbol,
                name=result.name,
                market=Market(result.market),
                industry=result.industry,
                list_date=result.list_date,
            )
        return None

    # ============== DailyQuote 操作 ==============

    def save_quotes(self, quotes: list[DailyQuote]):
        """批量保存日线行情"""
        if not quotes:
            return

        sql = """
        INSERT OR REPLACE INTO daily_quote
        (symbol, trade_date, open, high, low, close, volume, pre_close, amount, turnover_rate)
        VALUES
        (:symbol, :trade_date, :open, :high, :low, :close, :volume, :pre_close, :amount, :turnover_rate)
        """

        with self.engine.connect() as conn:
            for q in quotes:
                params = {
                    "symbol": q.symbol,
                    "trade_date": q.trade_date,
                    "open": float(q.open),
                    "high": float(q.high),
                    "low": float(q.low),
                    "close": float(q.close),
                    "volume": q.volume,
                    "pre_close": float(q.pre_close) if q.pre_close else None,
                    "amount": float(q.amount) if q.amount else None,
                    "turnover_rate": float(q.turnover_rate) if q.turnover_rate else None,
                }
                conn.execute(text(sql), params)
            conn.commit()
        logger.debug(f"Saved {len(quotes)} quotes")

    def get_quotes(self, symbol: str, days: int = 365) -> list[DailyQuote]:
        """获取指定天数的日线行情"""
        sql = """
        SELECT * FROM daily_quote
        WHERE symbol = :symbol
        AND trade_date >= :start_date
        ORDER BY trade_date ASC
        """

        start_date = date.today() - timedelta(days=days)

        with self.engine.connect() as conn:
            results = conn.execute(text(sql), {"symbol": symbol, "start_date": start_date}).fetchall()

        return [
            DailyQuote(
                symbol=r.symbol,
                trade_date=r.trade_date,
                open=Decimal(str(r.open)),
                high=Decimal(str(r.high)),
                low=Decimal(str(r.low)),
                close=Decimal(str(r.close)),
                volume=r.volume,
                pre_close=Decimal(str(r.pre_close)) if r.pre_close else None,
                amount=Decimal(str(r.amount)) if r.amount else None,
                turnover_rate=Decimal(str(r.turnover_rate)) if r.turnover_rate else None,
            )
            for r in results
        ]

    def get_latest_quote(self, symbol: str) -> DailyQuote | None:
        """获取最新日线行情"""
        sql = """
        SELECT * FROM daily_quote
        WHERE symbol = :symbol
        ORDER BY trade_date DESC
        LIMIT 1
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(sql), {"symbol": symbol}).fetchone()

        if result:
            return DailyQuote(
                symbol=result.symbol,
                trade_date=result.trade_date,
                open=Decimal(str(result.open)),
                high=Decimal(str(result.high)),
                low=Decimal(str(result.low)),
                close=Decimal(str(result.close)),
                volume=result.volume,
                pre_close=Decimal(str(result.pre_close)) if result.pre_close else None,
                amount=Decimal(str(result.amount)) if result.amount else None,
                turnover_rate=Decimal(str(result.turnover_rate)) if result.turnover_rate else None,
            )
        return None

    # ============== Financial 操作 ==============

    def save_financials(self, financials: list[Financial]):
        """批量保存财务数据"""
        if not financials:
            return

        sql = """
        INSERT OR REPLACE INTO financial
        (symbol, report_date, revenue, net_profit, total_assets, total_equity,
         roe, pe, pb, debt_ratio, gross_margin)
        VALUES
        (:symbol, :report_date, :revenue, :net_profit, :total_assets, :total_equity,
         :roe, :pe, :pb, :debt_ratio, :gross_margin)
        """

        with self.engine.connect() as conn:
            for f in financials:
                params = {
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
                }
                conn.execute(text(sql), params)
            conn.commit()
        logger.debug(f"Saved {len(financials)} financials")

    def get_financials(self, symbol: str, years: int = 5) -> list[Financial]:
        """获取指定年份的财务数据"""
        sql = """
        SELECT * FROM financial
        WHERE symbol = :symbol
        AND report_date >= :start_date
        ORDER BY report_date DESC
        """

        start_date = date.today() - timedelta(days=years * 365)

        with self.engine.connect() as conn:
            results = conn.execute(text(sql), {"symbol": symbol, "start_date": start_date}).fetchall()

        return [
            Financial(
                symbol=r.symbol,
                report_date=r.report_date,
                revenue=Decimal(str(r.revenue)) if r.revenue else None,
                net_profit=Decimal(str(r.net_profit)) if r.net_profit else None,
                total_assets=Decimal(str(r.total_assets)) if r.total_assets else None,
                total_equity=Decimal(str(r.total_equity)) if r.total_equity else None,
                roe=Decimal(str(r.roe)) if r.roe else None,
                pe=Decimal(str(r.pe)) if r.pe else None,
                pb=Decimal(str(r.pb)) if r.pb else None,
                debt_ratio=Decimal(str(r.debt_ratio)) if r.debt_ratio else None,
                gross_margin=Decimal(str(r.gross_margin)) if r.gross_margin else None,
            )
            for r in results
        ]

    # ============== Watchlist 操作 ==============

    def get_watchlist(self) -> list[WatchlistItem]:
        """获取所有自选股"""
        sql = "SELECT * FROM watchlist ORDER BY added_at DESC"

        with self.engine.connect() as conn:
            results = conn.execute(text(sql)).fetchall()

        return [
            WatchlistItem(
                symbol=r.symbol,
                added_at=r.added_at,
                notes=r.notes,
                alert_price_high=Decimal(str(r.alert_price_high)) if r.alert_price_high else None,
                alert_price_low=Decimal(str(r.alert_price_low)) if r.alert_price_low else None,
            )
            for r in results
        ]

    def add_to_watchlist(self, symbol: str, notes: str = None):
        """添加自选股"""
        sql = """
        INSERT OR REPLACE INTO watchlist (symbol, added_at, notes, alert_price_high, alert_price_low)
        VALUES (:symbol, :added_at, :notes, NULL, NULL)
        """

        with self.engine.connect() as conn:
            conn.execute(
                text(sql),
                {
                    "symbol": symbol,
                    "added_at": datetime.now(),
                    "notes": notes,
                },
            )
            conn.commit()
        logger.info(f"Added to watchlist: {symbol}")

    def remove_from_watchlist(self, symbol: str):
        """从自选股移除"""
        sql = "DELETE FROM watchlist WHERE symbol = :symbol"

        with self.engine.connect() as conn:
            conn.execute(text(sql), {"symbol": symbol})
            conn.commit()
        logger.info(f"Removed from watchlist: {symbol}")

    # ============== Alert 操作 ==============

    def save_alert(self, alert: Alert):
        """保存预警记录"""
        sql = """
        INSERT INTO alert (symbol, alert_type, message, triggered_at, is_read)
        VALUES (:symbol, :alert_type, :message, :triggered_at, :is_read)
        """

        with self.engine.connect() as conn:
            conn.execute(
                text(sql),
                {
                    "symbol": alert.symbol,
                    "alert_type": alert.alert_type.value,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at,
                    "is_read": alert.is_read,
                },
            )
            conn.commit()
        logger.info(f"Saved alert: {alert.alert_type.value} for {alert.symbol}")

    def get_alerts(self, limit: int = 50) -> list[Alert]:
        """获取预警记录"""
        sql = """
        SELECT * FROM alert
        ORDER BY triggered_at DESC
        LIMIT :limit
        """

        with self.engine.connect() as conn:
            results = conn.execute(text(sql), {"limit": limit}).fetchall()

        return [
            Alert(
                id=r.id,
                symbol=r.symbol,
                alert_type=AlertType(r.alert_type),
                message=r.message,
                triggered_at=r.triggered_at,
                is_read=bool(r.is_read),
            )
            for r in results
        ]

    # ============== DataSyncLog 操作 ==============

    def get_last_sync_date(self, data_type: str, market: str) -> date | None:
        """获取最后同步日期"""
        sql = """
        SELECT last_sync_date FROM data_sync_log
        WHERE data_type = :data_type AND market = :market
        """

        with self.engine.connect() as conn:
            result = conn.execute(
                text(sql),
                {"data_type": data_type, "market": market},
            ).fetchone()

        return result.last_sync_date if result else None

    def update_sync_log(self, data_type: str, market: str, sync_date: date):
        """更新同步日志"""
        sql = """
        INSERT OR REPLACE INTO data_sync_log (data_type, market, last_sync_date, updated_at)
        VALUES (:data_type, :market, :last_sync_date, :updated_at)
        """

        with self.engine.connect() as conn:
            conn.execute(
                text(sql),
                {
                    "data_type": data_type,
                    "market": market,
                    "last_sync_date": sync_date,
                    "updated_at": datetime.now(),
                },
            )
            conn.commit()
        logger.debug(f"Updated sync log: {data_type}/{market} -> {sync_date}")

    # ============== Account 操作 ==============

    def create_account(self, account) -> "Account":
        """创建账户"""
        from src.models.portfolio import Account

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO accounts (name, account_type, initial_capital, current_cash)
                VALUES (:name, :account_type, :initial_capital, :current_cash)
            """), {
                "name": account.name,
                "account_type": account.account_type.value if hasattr(account.account_type, "value") else account.account_type,
                "initial_capital": float(account.initial_capital),
                "current_cash": float(account.current_cash),
            })
            conn.commit()
            account.id = result.lastrowid
            return account

    def get_accounts(self) -> list["Account"]:
        """获取所有账户"""
        from src.models.portfolio import Account

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
        from src.models.portfolio import Account

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

    # ============== Transaction 操作 ==============

    def add_transaction(self, transaction) -> "Transaction":
        """添加交易记录"""
        from src.models.portfolio import Transaction

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO transactions (account_id, symbol, trade_type, shares, price, amount, fee, trade_date, notes)
                VALUES (:account_id, :symbol, :trade_type, :shares, :price, :amount, :fee, :trade_date, :notes)
            """), {
                "account_id": transaction.account_id,
                "symbol": transaction.symbol,
                "trade_type": transaction.trade_type.value if hasattr(transaction.trade_type, "value") else transaction.trade_type,
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
            cash_change = -transaction.amount if transaction.trade_type.value in ("买入", "BUY") else transaction.amount
            self.update_account_cash(transaction.account_id, cash_change)

            return transaction

    def get_transactions(self, account_id: int, limit: int = 100) -> list["Transaction"]:
        """获取交易记录"""
        from src.models.portfolio import Transaction, TradeType

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM transactions WHERE account_id = :account_id
                ORDER BY trade_date DESC, created_at DESC LIMIT :limit
            """), {"account_id": account_id, "limit": limit})
            transactions = []
            for row in result:
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

    def get_transactions_by_symbol(self, account_id: int, symbol: str) -> list["Transaction"]:
        """获取指定股票的交易记录"""
        from src.models.portfolio import Transaction, TradeType

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM transactions WHERE account_id = :account_id AND symbol = :symbol
                ORDER BY trade_date ASC
            """), {"account_id": account_id, "symbol": symbol})
            transactions = []
            for row in result:
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
