"""
K 线数据 - 日线/分钟线
支持周期: 1d / 60m / 30m / 15m / 5m / 1m
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import date, datetime, timedelta
import pandas as pd
from pathlib import Path
import json

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parents[5] / "data" / "kline"


def _load_kline_csv(ts_code: str, freq: str) -> Optional[pd.DataFrame]:
    """从本地 CSV 加载 (Tushare 同步后落地)"""
    file = DATA_DIR / f"{ts_code}_{freq}.csv"
    if not file.exists():
        return None
    try:
        df = pd.read_csv(file, parse_dates=["trade_date"])
        return df
    except Exception:
        return None


@router.get("/")
async def get_kline(
    ts_code: str = Query(..., description="股票代码, 如 000001.SZ"),
    freq: str = Query("1d", pattern="^(1d|60m|30m|15m|5m|1m)$"),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    limit: int = Query(500, le=5000),
):
    """
    获取 K 线数据
    - MVP 阶段从本地 CSV 读取 (scripts/fetch_history.py 同步)
    - 后续接 TimescaleDB 时序数据库
    """
    df = _load_kline_csv(ts_code, freq)
    if df is None or df.empty:
        return {
            "ts_code": ts_code,
            "freq": freq,
            "count": 0,
            "items": [],
            "_hint": "本地无数据, 请先运行 scripts/fetch_history.py 同步",
        }
    if start:
        df = df[df["trade_date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["trade_date"] <= pd.Timestamp(end)]
    df = df.sort_values("trade_date", ascending=False).head(limit)
    df = df.sort_values("trade_date", ascending=True)
    items = []
    for _, r in df.iterrows():
        items.append({
            "trade_date": r["trade_date"].strftime("%Y-%m-%d"),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "vol": int(r.get("vol", 0)),
            "amount": float(r.get("amount", 0)),
        })
    return {
        "ts_code": ts_code,
        "freq": freq,
        "count": len(items),
        "items": items,
    }


@router.get("/realtime/{ts_code}")
async def get_realtime(ts_code: str):
    """
    实时报价 (MVP: 返回最近一日的收盘价)
    V1.0: 接 WebSocket 推送 (Tushare / AkShare)
    """
    df = _load_kline_csv(ts_code.upper(), "1d")
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="无行情数据")
    last = df.sort_values("trade_date", ascending=False).iloc[0]
    return {
        "ts_code": ts_code,
        "trade_date": str(last["trade_date"].date()),
        "close": float(last["close"]),
        "_note": "MVP 阶段实时数据用最近日线收盘价占位",
    }
