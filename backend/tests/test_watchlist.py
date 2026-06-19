"""
测试: 自选股
"""
def test_list_watchlist(client):
    r = client.get("/api/v1/watchlist/")
    assert r.status_code == 200
    data = r.json()
    assert "groups" in data
    assert len(data["groups"]) >= 1


def test_add_and_remove(client):
    # 添加
    r = client.post("/api/v1/watchlist/", json={
        "ts_code": "600519.SH", "name": "贵州茅台", "group": "默认分组"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    # 重复添加应报错
    r2 = client.post("/api/v1/watchlist/", json={
        "ts_code": "600519.SH", "name": "贵州茅台", "group": "默认分组"
    })
    assert r2.status_code == 400
    # 删除
    r3 = client.delete("/api/v1/watchlist/600519.SH?group=默认分组")
    assert r3.status_code == 200
