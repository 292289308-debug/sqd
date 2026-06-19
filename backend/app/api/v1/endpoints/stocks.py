"""
股票基础信息 - 列表/搜索/详情
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import json
import os
from pathlib import Path

router = APIRouter()

# 简单实现: 从本地文件加载股票列表 (后续接 Tushare stock_basic)
_STOCKS_CACHE: Optional[list] = None


def _load_stocks():
    global _STOCKS_CACHE
    if _STOCKS_CACHE is not None:
        return _STOCKS_CACHE
    data_dir = Path(__file__).resolve().parents[5] / "data"
    # 加载 demo (补 name 补业) + top100/stocks.json
    demo_map = {}
    demo_path = data_dir / "stocks_demo.json"
    if demo_path.exists():
        for s in json.loads(demo_path.read_text(encoding="utf-8")):
            demo_map[s["ts_code"]] = s
    # 优先级: stocks.json > top100.json > stocks_demo.json
    items = []
    for filename in ("stocks.json", "top100.json"):
        path = data_dir / filename
        if path.exists():
            try:
                items = json.loads(path.read_text(encoding="utf-8"))
                break
            except Exception as e:
                print(f"[_load_stocks] {filename} parse err: {e}")
    if not items:
        items = list(demo_map.values())
    # 补齐 name/industry
    normalized = []
    for s in items:
        ts_code = s.get("ts_code", "")
        sym = ts_code.split(".")[0] if ts_code else ""
        mkt = ts_code.split(".")[-1] if ts_code else ""
        # 从 demo 补 name/industry
        demo = demo_map.get(ts_code, {})
        normalized.append({
            "ts_code": ts_code,
            "symbol": sym,
            "name": s.get("name") or demo.get("name", ""),
            "industry": s.get("industry") or demo.get("industry", ""),
            "list_date": s.get("list_date", ""),
            "market": s.get("market", mkt),
        })
    _STOCKS_CACHE = normalized
    return _STOCKS_CACHE


@router.get("/")
async def list_stocks(
    market: Optional[str] = Query(None, description="SZ/SH/HK"),
    industry: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None, description="代码或名称模糊搜索"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
):
    """股票列表 (分页+筛选)"""
    stocks = _load_stocks()
    if market:
        stocks = [s for s in stocks if s.get("market") == market.upper()]
    if industry:
        stocks = [s for s in stocks if industry in (s.get("industry") or "")]
    if keyword:
        kw = keyword.upper()
        stocks = [s for s in stocks if kw in s["ts_code"] or kw in s["name"]]
    total = len(stocks)
    return {
        "total": total,
        "items": stocks[offset:offset + limit],
    }


@router.get("/{ts_code}")
async def get_stock(ts_code: str):
    """单只股票详情"""
    for s in _load_stocks():
        if s["ts_code"] == ts_code.upper():
            return s
    raise HTTPException(status_code=404, detail=f"股票不存在: {ts_code}")
