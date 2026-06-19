"""
策略管理 - 列出/创建/获取策略
MVP 阶段: 30 个内置模板 + 用户自定义
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
from pathlib import Path

router = APIRouter()

TEMPLATES_FILE = Path(__file__).resolve().parents[5] / "data" / "strategies_demo.json"


def _load_demo():
    """加载 demo JSON (包含代码示例)"""
    if not TEMPLATES_FILE.exists():
        return {}
    items = json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))
    return {t["id"]: t for t in items}


def _get_engine_strategies():
    """从引擎动态加载策略定义"""
    from app.services.backtest_engine import STRATEGIES
    return STRATEGIES


@router.get("/templates")
async def list_templates(category: Optional[str] = None):
    """内置策略模板 - 从 backtest_engine 动态加载"""
    strategies = _get_engine_strategies()
    items = []
    for sid, meta in strategies.items():
        item = {
            "id": sid,
            "name": meta["name"],
            "category": meta["category"],
            "description": meta["description"],
            "params": meta["params"],
        }
        items.append(item)
    if category:
        items = [i for i in items if i["category"] == category]
    return {"count": len(items), "items": items}


@router.get("/templates/{strategy_id}")
async def get_template(strategy_id: str):
    strategies = _get_engine_strategies()
    if strategy_id not in strategies:
        raise HTTPException(404, "策略不存在")
    meta = strategies[strategy_id]
    # 附带 demo 代码
    demo = _load_demo()
    code = demo.get(strategy_id, {}).get("code", "# 见 app/services/backtest_engine.py")
    return {
        "id": strategy_id,
        "name": meta["name"],
        "category": meta["category"],
        "description": meta["description"],
        "params": meta["params"],
        "code": code,
    }


class CustomStrategy(BaseModel):
    name: str
    category: str
    description: str = ""
    code: str
    params: dict = {}


# MVP 阶段: 内存存储 (重启清空) - V1.0 接数据库
_user_strategies: List[dict] = []


@router.get("/")
async def list_user_strategies():
    return {"count": len(_user_strategies), "items": _user_strategies}


@router.post("/")
async def create_strategy(s: CustomStrategy):
    sid = f"u_{len(_user_strategies) + 1:04d}"
    item = {
        "id": sid,
        "name": s.name,
        "category": s.category,
        "description": s.description,
        "code": s.code,
        "params": s.params,
    }
    _user_strategies.append(item)
    return item
