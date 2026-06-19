"""
自选股 - MVP 阶段用本地文件存储 (单用户演示)
后续接数据库 + 多用户
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path

router = APIRouter()

DATA_FILE = Path(__file__).resolve().parents[5] / "data" / "watchlist_demo.json"


def _load():
    if not DATA_FILE.exists():
        return {"groups": [{"name": "默认分组", "items": []}]}
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def _save(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class AddItem(BaseModel):
    ts_code: str
    name: str
    group: str = "默认分组"


@router.get("/")
async def list_watchlist():
    return _load()


@router.post("/")
async def add_item(item: AddItem):
    data = _load()
    # 找分组
    group = next((g for g in data["groups"] if g["name"] == item.group), None)
    if not group:
        group = {"name": item.group, "items": []}
        data["groups"].append(group)
    if any(x["ts_code"] == item.ts_code for x in group["items"]):
        raise HTTPException(400, "已在自选股中")
    group["items"].append({"ts_code": item.ts_code, "name": item.name})
    _save(data)
    return {"ok": True, "groups": data["groups"]}


@router.delete("/{ts_code}")
async def remove_item(ts_code: str, group: str = "默认分组"):
    data = _load()
    for g in data["groups"]:
        g["items"] = [x for x in g["items"] if x["ts_code"] != ts_code]
    _save(data)
    return {"ok": True}
