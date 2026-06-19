-- ============================================================
-- 灵眸量化 - 数据库初始化 (TimescaleDB + PostgreSQL)
-- 启动时由 docker-entrypoint-initdb.d 自动执行
-- ============================================================

-- 启用 TimescaleDB 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================
-- 1. 用户与认证
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(64) UNIQUE NOT NULL,
    email           VARCHAR(128) UNIQUE,
    password_hash   VARCHAR(256) NOT NULL,
    display_name    VARCHAR(64),
    is_active       BOOLEAN DEFAULT TRUE,
    is_admin        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================================
-- 2. 股票基础信息 (维度表)
-- ============================================================
CREATE TABLE IF NOT EXISTS stocks (
    ts_code         VARCHAR(16) PRIMARY KEY,   -- 000001.SZ
    symbol          VARCHAR(16) NOT NULL,      -- 000001
    name            VARCHAR(64) NOT NULL,      -- 平安银行
    industry        VARCHAR(64),              -- 银行
    list_date       DATE,
    market          VARCHAR(8) NOT NULL,       -- SZ/SH/HK
    is_active       BOOLEAN DEFAULT TRUE,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stocks_industry ON stocks(industry);
CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market);

-- ============================================================
-- 3. K 线行情 (TimescaleDB hypertable)
-- ============================================================
CREATE TABLE IF NOT EXISTS kline_daily (
    ts_code         VARCHAR(16) NOT NULL,
    trade_date      DATE NOT NULL,
    open            NUMERIC(12,4) NOT NULL,
    high            NUMERIC(12,4) NOT NULL,
    low             NUMERIC(12,4) NOT NULL,
    close           NUMERIC(12,4) NOT NULL,
    pre_close       NUMERIC(12,4),
    change          NUMERIC(12,4),
    pct_chg         NUMERIC(8,4),
    vol             BIGINT,            -- 成交量(手)
    amount          NUMERIC(18,4),     -- 成交额(千元)
    turnover_rate   NUMERIC(8,4),      -- 换手率 %
    pe              NUMERIC(12,4),     -- 动态市盈率
    pb              NUMERIC(12,4),
    PRIMARY KEY (ts_code, trade_date)
);

-- 转为 hypertable (按月分区)
SELECT create_hypertable('kline_daily', 'trade_date',
       chunk_time_interval => INTERVAL '1 year',
       if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_kline_daily_code ON kline_daily(ts_code, trade_date DESC);

-- ============================================================
-- 4. 分钟 K 线 (高频数据,空间占用大)
-- ============================================================
CREATE TABLE IF NOT EXISTS kline_minute (
    ts_code         VARCHAR(16) NOT NULL,
    trade_time      TIMESTAMPTZ NOT NULL,    -- 含时分秒
    open            NUMERIC(12,4) NOT NULL,
    high            NUMERIC(12,4) NOT NULL,
    low             NUMERIC(12,4) NOT NULL,
    close           NUMERIC(12,4) NOT NULL,
    vol             BIGINT,
    amount          NUMERIC(18,4),
    PRIMARY KEY (ts_code, trade_time)
);

SELECT create_hypertable('kline_minute', 'trade_time',
       chunk_time_interval => INTERVAL '1 month',
       if_not_exists => TRUE);

-- ============================================================
-- 5. 自选股
-- ============================================================
CREATE TABLE IF NOT EXISTS watchlist (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_name      VARCHAR(64) DEFAULT '默认分组',
    ts_code         VARCHAR(16) NOT NULL REFERENCES stocks(ts_code),
    sort_order      INT DEFAULT 0,
    note            VARCHAR(256),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, group_name, ts_code)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id, group_name);

-- ============================================================
-- 6. 策略定义
-- ============================================================
CREATE TABLE IF NOT EXISTS strategies (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(128) NOT NULL,
    description     TEXT,
    category        VARCHAR(32),              -- trend/mean_reversion/factor/...
    code            TEXT,                     -- Python 策略源码
    params          JSONB DEFAULT '{}',       -- 策略参数
    is_public       BOOLEAN DEFAULT FALSE,    -- 是否发布到策略市场
    is_template     BOOLEAN DEFAULT FALSE,    -- 是否内置模板
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_strategies_user ON strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_strategies_category ON strategies(category);

-- ============================================================
-- 7. 回测任务与结果
-- ============================================================
CREATE TABLE IF NOT EXISTS backtest_runs (
    id              BIGSERIAL PRIMARY KEY,
    strategy_id     BIGINT NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    status          VARCHAR(16) DEFAULT 'pending',  -- pending/running/done/failed
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    universe        JSONB,                    -- 股票池 [ts_code, ...]
    benchmark       VARCHAR(16) DEFAULT '000300.SH',  -- 沪深300
    initial_cash    NUMERIC(18,2) DEFAULT 1000000,
    commission_rate NUMERIC(8,4) DEFAULT 0.0003,
    slippage        NUMERIC(8,4) DEFAULT 0.001,
    -- 结果指标
    total_return    NUMERIC(10,4),
    annual_return   NUMERIC(10,4),
    sharpe_ratio    NUMERIC(10,4),
    max_drawdown    NUMERIC(10,4),
    win_rate        NUMERIC(8,4),
    trade_count     INT,
    -- 详细结果 (JSON,可能很大)
    equity_curve    JSONB,
    trades          JSONB,
    metrics         JSONB,
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backtest_user ON backtest_runs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON backtest_runs(strategy_id);

-- ============================================================
-- 8. 模拟盘 / 实盘持仓 (V1.1 启用)
-- ============================================================
CREATE TABLE IF NOT EXISTS accounts (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    broker          VARCHAR(32),              -- CTP/XTP/UFT
    account_no      VARCHAR(64),
    account_type    VARCHAR(16) DEFAULT 'simulation',  -- simulation/live
    initial_cash    NUMERIC(18,2),
    current_cash    NUMERIC(18,2),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS positions (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    ts_code         VARCHAR(16) NOT NULL,
    quantity        BIGINT NOT NULL,
    avg_cost        NUMERIC(12,4) NOT NULL,
    current_price   NUMERIC(12,4),
    market_value    NUMERIC(18,4),
    profit          NUMERIC(18,4),
    profit_pct      NUMERIC(8,4),
    opened_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT NOT NULL REFERENCES accounts(id),
    ts_code         VARCHAR(16) NOT NULL,
    side            VARCHAR(8) NOT NULL,      -- buy/sell
    order_type      VARCHAR(16) DEFAULT 'limit',  -- market/limit/twap/vwap
    quantity        BIGINT NOT NULL,
    price           NUMERIC(12,4),
    filled_qty      BIGINT DEFAULT 0,
    filled_avg_price NUMERIC(12,4),
    status          VARCHAR(16) DEFAULT 'pending',  -- pending/filled/cancelled/failed
    strategy_id     BIGINT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_account ON orders(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_positions_account ON positions(account_id);

-- ============================================================
-- 9. 资讯/研报 (V1.2 启用)
-- ============================================================
CREATE TABLE IF NOT EXISTS news (
    id              BIGSERIAL PRIMARY KEY,
    source          VARCHAR(32) NOT NULL,     -- 财联社/雪球/...
    title           VARCHAR(256) NOT NULL,
    url             TEXT,
    content         TEXT,
    ts_codes        TEXT[],                   -- 关联股票
    sentiment_score NUMERIC(5,4),             -- -1 ~ 1
    published_at    TIMESTAMPTZ NOT NULL,
    crawled_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_codes ON news USING GIN(ts_codes);

-- ============================================================
-- 10. 系统配置 / 缓存
-- ============================================================
CREATE TABLE IF NOT EXISTS system_meta (
    key             VARCHAR(64) PRIMARY KEY,
    value           JSONB,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 插入初始元数据
INSERT INTO system_meta (key, value) VALUES
    ('schema_version', '"0.1.0"'::jsonb),
    ('last_kline_sync', 'null'::jsonb),
    ('data_coverage', '{"a_share_daily": "2010-2026"}'::jsonb)
ON CONFLICT (key) DO NOTHING;

-- ============================================================
-- 完成
-- ============================================================
COMMENT ON SCHEMA public IS '灵眸量化 v0.1 - 2026-06-19';
