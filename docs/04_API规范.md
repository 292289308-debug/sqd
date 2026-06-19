# API 规范 (v1)

**Base URL**: `http://127.0.0.1:8000`  
**前缀**: `/api/v1`  
**格式**: JSON  
**认证**: MVP 阶段无；V1.0 起 JWT（Bearer Token）

---

## 1. 元信息

### GET /health
健康检查
```json
{"status": "ok", "name": "灵眸量化", "version": "0.1.0", "ts": "2026-06-19T07:32:49"}
```

### GET /config
前端配置（脱敏）
```json
{"appName": "灵眸量化", "version": "0.1.0", "hasTushareToken": false, "dataDir": "./data"}
```

---

## 2. 股票 (stocks)

### GET /stocks/
列表 + 搜索 + 筛选
| 参数 | 类型 | 说明 |
|---|---|---|
| market | string | SZ / SH / HK |
| industry | string | 行业关键字 |
| keyword | string | 代码或名称模糊搜索 |
| limit | int | 默认 50，max 500 |
| offset | int | 默认 0 |

**响应**:
```json
{"total": 10, "items": [{"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "industry": "银行", "list_date": "19910403", "market": "SZ"}]}
```

### GET /stocks/{ts_code}
单只股票详情

---

## 3. K 线 (kline)

### GET /kline/
| 参数 | 必填 | 说明 |
|---|---|---|
| ts_code | 是 | 股票代码 |
| freq | 是 | 1d / 60m / 30m / 15m / 5m / 1m |
| start | 否 | YYYY-MM-DD |
| end | 否 | YYYY-MM-DD |
| limit | 否 | 默认 500，max 5000 |

**响应**:
```json
{
  "ts_code": "600519.SH",
  "freq": "1d",
  "count": 3,
  "items": [
    {"trade_date": "2026-06-17", "open": 102.77, "high": 106.04, "low": 101.38, "close": 103.40, "vol": 5513739, "amount": 287772.62}
  ]
}
```

### GET /kline/realtime/{ts_code}
最近一个交易日的收盘价（实时数据接入前占位）

---

## 4. 自选股 (watchlist)

### GET /watchlist/
返回所有分组 + 股票
```json
{"groups": [{"name": "银行", "items": [{"ts_code": "600036.SH", "name": "招商银行"}]}]}
```

### POST /watchlist/
添加股票到分组
```json
// request
{"ts_code": "600519.SH", "name": "贵州茅台", "group": "默认分组"}
// response
{"ok": true, "groups": [...]}
```

### DELETE /watchlist/{ts_code}?group=默认分组
删除

---

## 5. 策略 (strategy)

### GET /strategy/templates?category=trend
内置策略模板列表
```json
{
  "count": 6,
  "items": [
    {"id": "dual_ma_5_20", "name": "双均线 (5/20)", "category": "trend", "description": "...", "params": {"short": 5, "long": 20}}
  ]
}
```

### GET /strategy/templates/{strategy_id}
单个策略详情（含 code 字段）

### GET /strategy/
用户自定义策略列表

### POST /strategy/
创建用户策略
```json
{
  "name": "我的策略",
  "category": "trend",
  "description": "...",
  "code": "...",
  "params": {}
}
```

---

## 6. 回测 (backtest)

### POST /backtest/run
提交回测任务（MVP 同步执行）

**请求体**:
```json
{
  "strategy_id": "dual_ma_5_20",
  "start_date": "2026-04-01",
  "end_date": "2026-06-19",
  "universe": ["600519.SH"],
  "benchmark": "000300.SH",
  "initial_cash": 1000000,
  "commission_rate": 0.0003,
  "slippage": 0.001
}
```

**响应**:
```json
{
  "main_code": "600519.SH",
  "trade_count": 3,
  "trades": [
    {"date": "2026-04-29", "code": "600519.SH", "side": "buy", "price": 100.66}
  ],
  "equity_curve": [
    {"date": "2026-04-01", "nav": 1000000.0, "benchmark": 1000000.0, "position": 0}
  ],
  "metrics": {
    "total_return": 0.0084,
    "annual_return": 0.0369,
    "benchmark_return": 0.0003,
    "alpha": 0.0366,
    "sharpe_ratio": 0.69,
    "max_drawdown": -0.0184,
    "trade_days": 58,
    "trade_count": 3,
    "win_rate": 0
  }
}
```

### GET /backtest/runs?limit=20
历史回测任务列表

### GET /backtest/runs/{run_id}
查询单个回测结果

---

## 7. 错误响应

```json
{"detail": "股票不存在: 999999.SZ"}
```

| HTTP Code | 含义 |
|---|---|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 参数验证失败（Pydantic） |
| 500 | 服务器内部错误 |

---

## 8. 后续扩展

- [ ] WebSocket `/ws/quote/{ts_code}` 实时行情
- [ ] WebSocket `/ws/backtest/{run_id}` 回测进度
- [ ] 认证 `/auth/login` `/auth/register`
- [ ] 实盘 `/broker/account` `/broker/order` (V1.1)
- [ ] 资讯 `/news/?ts_code=...` (V1.2)
