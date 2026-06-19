"""
测试: 股票列表 / 搜索
"""
def test_list_stocks(client):
    r = client.get("/api/v1/stocks/")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "items" in data
    # demo 数据至少有 10 只
    assert data["total"] >= 10


def test_search_by_keyword(client):
    r = client.get("/api/v1/stocks/?keyword=茅台")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    # 至少匹配到一个含"茅台"的
    assert any("茅台" in s["name"] for s in data["items"])


def test_filter_by_market(client):
    r = client.get("/api/v1/stocks/?market=SH")
    assert r.status_code == 200
    data = r.json()
    for s in data["items"]:
        assert s["market"] == "SH"


def test_get_stock_detail(client):
    r = client.get("/api/v1/stocks/600519.SH")
    assert r.status_code == 200
    data = r.json()
    assert data["ts_code"] == "600519.SH"
    assert data["name"] == "贵州茅台"


def test_get_stock_404(client):
    r = client.get("/api/v1/stocks/999999.SZ")
    assert r.status_code == 404


def test_pagination(client):
    r1 = client.get("/api/v1/stocks/?limit=3&offset=0")
    r2 = client.get("/api/v1/stocks/?limit=3&offset=3")
    assert r1.status_code == 200
    assert r2.status_code == 200
    d1 = r1.json()
    d2 = r2.json()
    assert len(d1["items"]) == 3
    assert len(d2["items"]) == 3
    # 不重叠
    codes1 = {s["ts_code"] for s in d1["items"]}
    codes2 = {s["ts_code"] for s in d2["items"]}
    assert codes1.isdisjoint(codes2)
