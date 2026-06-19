"""
测试: 策略管理
"""
def test_list_templates(client):
    r = client.get("/api/v1/strategy/templates")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 5
    # 每个模板有必需字段
    for t in data["items"]:
        assert {"id", "name", "category", "description"} <= t.keys()


def test_filter_by_category(client):
    r = client.get("/api/v1/strategy/templates?category=trend")
    assert r.status_code == 200
    data = r.json()
    for t in data["items"]:
        assert t["category"] == "trend"


def test_get_template(client):
    r = client.get("/api/v1/strategy/templates/dual_ma_5_20")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "dual_ma_5_20"
    assert "params" in data


def test_create_user_strategy(client):
    r = client.post("/api/v1/strategy/", json={
        "name": "我的测试策略",
        "category": "trend",
        "description": "测试",
        "code": "def on_bar(ctx): pass",
        "params": {"a": 1}
    })
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "我的测试策略"
    assert data["id"].startswith("u_")
