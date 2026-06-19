"""
数据接入 - Tushare Pro / AkShare

MVP 阶段: 拉一次日线 → 存 CSV → 后续从 CSV 读
V1.0: 增量同步 + TimescaleDB 持久化 + Celery 定时任务
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

from app.core.config import settings


DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "kline"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_stock_basic() -> pd.DataFrame:
    """
    拉股票基础信息 (Tushare stock_basic)
    返回: ts_code, symbol, name, industry, list_date, market
    """
    token = settings.TUSHARE_TOKEN
    if not token or token == "your_tushare_token_here":
        # 无 token: 返回内置 demo
        return _demo_stocks()

    try:
        import tushare as ts
        ts.set_token(token)
        pro = ts.pro_api()
        df = pro.stock_basic(
            list_status="L",
            fields="ts_code,symbol,name,industry,list_date,market",
        )
        return df
    except ImportError:
        return _demo_stocks()
    except Exception as e:
        print(f"[fetch_stock_basic] 失败: {e}")
        return _demo_stocks()


def fetch_daily_kline(ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    拉日 K 线 → 存 CSV
    start_date / end_date 格式: '20250101'
    """
    token = settings.TUSHARE_TOKEN
    if not token or token == "your_tushare_token_here":
        return _demo_kline(ts_code)

    try:
        import tushare as ts
        ts.set_token(token)
        pro = ts.pro_api()
        df = pro.daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
        )
        if df is None or df.empty:
            return pd.DataFrame()
        # 落地 CSV
        df = df.sort_values("trade_date")
        out = DATA_DIR / f"{ts_code}_1d.csv"
        df.to_csv(out, index=False, encoding="utf-8")
        return df
    except ImportError:
        return _demo_kline(ts_code)
    except Exception as e:
        print(f"[fetch_daily_kline] {ts_code} 失败: {e}")
        return pd.DataFrame()


def _demo_stocks() -> pd.DataFrame:
    """内置 demo 股票池 (无 Tushare token 时使用)"""
    data = [
        {"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "industry": "银行", "list_date": "19910403", "market": "SZ"},
        {"ts_code": "000002.SZ", "symbol": "000002", "name": "万科A", "industry": "房地产", "list_date": "19910129", "market": "SZ"},
        {"ts_code": "000333.SZ", "symbol": "000333", "name": "美的集团", "industry": "家电", "list_date": "20130918", "market": "SZ"},
        {"ts_code": "000858.SZ", "symbol": "000858", "name": "五粮液", "industry": "白酒", "list_date": "19980427", "market": "SZ"},
        {"ts_code": "600000.SH", "symbol": "600000", "name": "浦发银行", "industry": "银行", "list_date": "19991110", "market": "SH"},
        {"ts_code": "600036.SH", "symbol": "600036", "name": "招商银行", "industry": "银行", "list_date": "20020409", "market": "SH"},
        {"ts_code": "600519.SH", "symbol": "600519", "name": "贵州茅台", "industry": "白酒", "list_date": "20010827", "market": "SH"},
        {"ts_code": "600887.SH", "symbol": "600887", "name": "伊利股份", "industry": "食品", "list_date": "19960312", "market": "SH"},
        {"ts_code": "601318.SH", "symbol": "601318", "name": "中国平安", "industry": "保险", "list_date": "20070301", "market": "SH"},
        {"ts_code": "601398.SH", "symbol": "601398", "name": "工商银行", "industry": "银行", "list_date": "20061027", "market": "SH"},
    ]
    return pd.DataFrame(data)


def _demo_kline(ts_code: str) -> pd.DataFrame:
    """内置 demo K 线 (随机生成 60 个交易日, 后续接 Tushare)"""
    import numpy as np
    np.random.seed(hash(ts_code) % 2**32)
    n = 60
    base = 10 + (hash(ts_code) % 90) + np.random.randn(n).cumsum() * 0.5
    base = np.abs(base) + 5
    dates = pd.bdate_range(end=datetime.now().date(), periods=n)
    df = pd.DataFrame({
        "trade_date": dates.strftime("%Y%m%d"),
        "open": (base * (1 + np.random.uniform(-0.01, 0.01, n))).round(2),
        "high": (base * (1 + np.random.uniform(0, 0.03, n))).round(2),
        "low": (base * (1 - np.random.uniform(0, 0.03, n))).round(2),
        "close": base.round(2),
        "pre_close": (base * (1 + np.random.uniform(-0.01, 0.01, n))).round(2),
        "change": (np.random.uniform(-1, 1, n)).round(3),
        "pct_chg": (np.random.uniform(-3, 3, n)).round(3),
        "vol": (np.random.randint(100000, 10000000, n)),
        "amount": (base * np.random.randint(100000, 10000000, n) / 1000).round(2),
    })
    out = DATA_DIR / f"{ts_code}_1d.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    return df
