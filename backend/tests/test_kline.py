"""
测试: K 线 API
"""
def test_get_daily_kline(client):
    r = client.get("/api/v1/kline/?ts_code=600519.SH&freq=1d&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert data["ts_code"] == "600519.SH"
    assert data["freq"] == "1d"
    assert data["count"] > 0
    # 验证 OHLC 数据结构
    k = data["items"][0]
    assert {"trade_date", "open", "high", "low", "close"} <= k.keys()
    assert k["high"] >= k["low"]
    assert k["open"] > 0


def test_kline_freq_validation(client):
    """freq 必须是合法值"""
    r = client.get("/api/v1/kline/?ts_code=600519.SH&freq=invalid")
    assert r.status_code == 422


def test_kline_limit_max(client):
    """limit 不能超过 5000"""
    r = client.get("/api/v1/kline/?ts_code=600519.SH&limit=10000")
    assert r.status_code == 422


def test_kline_date_range(client):
    """日期过滤"""
    r = client.get("/api/v1/kline/?ts_code=600519.SH&start=2026-06-01&end=2026-06-19")
    assert r.status_code == 200
    data = r.json()
    for k in data["items"]:
        assert "2026-06-01" <= k["trade_date"] <= "2026-06-19"


def test_kline_realtime(client):
    r = client.get("/api/v1/kline/realtime/600519.SH")
    assert r.status_code == 200
    data = r.json()
    assert data["ts_code"] == "600519.SH"
    assert data["close"] > 0
