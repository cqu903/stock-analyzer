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
