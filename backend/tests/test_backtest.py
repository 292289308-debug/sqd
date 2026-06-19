"""
测试: 回测 API + 引擎
"""
def test_backtest_dual_ma(client):
    """贵州茅台双均线回测"""
    r = client.post("/api/v1/backtest/run", json={
        "strategy_id": "dual_ma_5_20",
        "start_date": "2026-04-01",
        "end_date": "2026-06-19",
        "universe": ["600519.SH"],
        "initial_cash": 1000000,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["main_code"] == "600519.SH"
    m = data["metrics"]
    assert m["trade_days"] > 0
    assert "total_return" in m
    assert "sharpe_ratio" in m
    assert "max_drawdown" in m
    # 回测有交易
    assert data["trade_count"] >= 1


def test_backtest_empty_universe(client):
    r = client.post("/api/v1/backtest/run", json={
        "strategy_id": "dual_ma_5_20",
        "start_date": "2026-04-01",
        "end_date": "2026-06-19",
        "universe": [],
        "initial_cash": 1000000,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["trade_count"] == 0
    assert data["metrics"]["total_return"] == 0


def test_backtest_invalid_date(client):
    r = client.post("/api/v1/backtest/run", json={
        "strategy_id": "dual_ma_5_20",
        "start_date": "2026-12-31",
        "end_date": "2026-01-01",  # 倒序
        "universe": ["600519.SH"],
    })
    assert r.status_code == 200  # MVP 不严格校验
    # 但应该返回空结果
    data = r.json()
    assert data["metrics"]["trade_days"] == 0


def test_list_runs(client):
    """先跑一个再查列表"""
    client.post("/api/v1/backtest/run", json={
        "strategy_id": "dual_ma_5_20",
        "start_date": "2026-04-01",
        "end_date": "2026-06-19",
        "universe": ["600519.SH"],
    })
    r = client.get("/api/v1/backtest/runs")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1


def test_engine_metrics():
    """直接测引擎函数"""
    from app.services.backtest_engine import BacktestEngine
    from datetime import date
    engine = BacktestEngine(initial_cash=1_000_000)
    result = engine.run_dual_ma(
        date(2026, 4, 1), date(2026, 6, 19),
        ["600519.SH"], "dual_ma_5_20"
    )
    assert result["main_code"] == "600519.SH"
    assert result["metrics"]["trade_days"] > 0
    # max_drawdown 应该是负数或 0
    assert result["metrics"]["max_drawdown"] <= 0
