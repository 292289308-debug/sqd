"""
测试: 健康检查 + 元信息
"""
def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "灵眸量化" in data["name"]
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "ts" in data


def test_config(client):
    r = client.get("/api/v1/health/config")
    assert r.status_code == 200
    data = r.json()
    assert data["appName"] == "灵眸量化"
    assert "hasTushareToken" in data
