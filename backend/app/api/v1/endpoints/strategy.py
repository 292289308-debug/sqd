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


def _load_templates():
    if not TEMPLATES_FILE.exists():
        return []
    return json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))


@router.get("/templates")
async def list_templates(category: Optional[str] = None):
    """内置策略模板"""
    templates = _load_templates()
    if category:
        templates = [t for t in templates if t.get("category") == category]
    return {"count": len(templates), "items": templates}


@router.get("/templates/{strategy_id}")
async def get_template(strategy_id: str):
    for t in _load_templates():
        if t["id"] == strategy_id:
            return t
    raise HTTPException(404, "策略不存在")


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
