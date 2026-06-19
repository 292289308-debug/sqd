"""
pytest 公共 fixtures
"""
import sys
from pathlib import Path
import pytest

# 把 backend 加到 path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI 测试客户端"""
    return TestClient(app)


@pytest.fixture
def sample_stock():
    """示例股票数据"""
    return {"ts_code": "600519.SH", "name": "贵州茅台", "industry": "白酒"}
