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
    # 内置一个最小的演示列表 (后续 Tushare stock_basic 全量同步)
    demo_path = Path(__file__).resolve().parents[5] / "data" / "stocks_demo.json"
    if demo_path.exists():
        _STOCKS_CACHE = json.loads(demo_path.read_text(encoding="utf-8"))
    else:
        _STOCKS_CACHE = []
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
