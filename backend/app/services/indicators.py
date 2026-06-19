"""
技术指标计算服务
支持: MA / EMA / MACD / RSI / BOLL / KDJ
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


def calc_ma(close: pd.Series, period: int) -> pd.Series:
    """简单移动平均"""
    return close.rolling(period).mean().fillna(0)


def calc_ema(close: pd.Series, period: int) -> pd.Series:
    """指数移动平均"""
    return close.ewm(span=period, adjust=False).mean().fillna(0)


def calc_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD 指标
    返回: (DIF, DEA, HIST)
    """
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = (dif - dea) * 2
    return dif.fillna(0), dea.fillna(0), hist.fillna(0)


def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI 指标"""
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - 100 / (1 + rs)
    return rsi.fillna(50)


def calc_boll(close: pd.Series, period: int = 20, std_n: float = 2.0):
    """布林带
    返回: (MID, UPPER, LOWER)
    """
    mid = close.rolling(period).mean()
    sigma = close.rolling(period).std()
    upper = mid + std_n * sigma
    lower = mid - std_n * sigma
    return mid.fillna(0), upper.fillna(0), lower.fillna(0)


def calc_kdj(high: pd.Series, low: pd.Series, close: pd.Series,
             n: int = 9, k_period: int = 3, d_period: int = 3):
    """KDJ 指标
    返回: (K, D, J)
    """
    low_n = low.rolling(n).min()
    high_n = high.rolling(n).max()
    rsv = (close - low_n) / (high_n - low_n + 1e-9) * 100
    k = rsv.ewm(alpha=1/k_period, adjust=False).mean()
    d = k.ewm(alpha=1/d_period, adjust=False).mean()
    j = 3 * k - 2 * d
    return k.fillna(50), d.fillna(50), j.fillna(50)


def attach_indicators(df: pd.DataFrame, indicators: List[str]) -> pd.DataFrame:
    """给 K 线 df 附加指标列
    df 必须含: trade_date, open, high, low, close, vol
    返回的 df 多了相应指标列
    """
    df = df.copy()
    close = df["close"]
    high = df["high"]
    low = df["low"]
    vol = df["vol"]

    for ind in indicators:
        if ind == "MA5":
            df["MA5"] = calc_ma(close, 5)
        elif ind == "MA10":
            df["MA10"] = calc_ma(close, 10)
        elif ind == "MA20":
            df["MA20"] = calc_ma(close, 20)
        elif ind == "MA60":
            df["MA60"] = calc_ma(close, 60)
        elif ind == "EMA12":
            df["EMA12"] = calc_ema(close, 12)
        elif ind == "EMA26":
            df["EMA26"] = calc_ema(close, 26)
        elif ind == "MACD":
            dif, dea, hist = calc_macd(close)
            df["MACD_DIF"] = dif
            df["MACD_DEA"] = dea
            df["MACD_HIST"] = hist
        elif ind == "RSI":
            df["RSI14"] = calc_rsi(close, 14)
        elif ind == "BOLL":
            mid, upper, lower = calc_boll(close)
            df["BOLL_MID"] = mid
            df["BOLL_UPPER"] = upper
            df["BOLL_LOWER"] = lower
        elif ind == "KDJ":
            k, d, j = calc_kdj(high, low, close)
            df["KDJ_K"] = k
            df["KDJ_D"] = d
            df["KDJ_J"] = j
        elif ind == "VOL_MA5":
            df["VOL_MA5"] = vol.rolling(5).mean().fillna(0)
    return df
