"""
回测引擎 MVP v0.2 - 多策略支持

支持策略:
- dual_ma_5_20: 双均线 (5/20)
- dual_ma_10_30: 双均线 (10/30)
- turtle_breakout: 海龟突破 (20日新高买入, 10日新低卖出)
- bollinger_revert: 布林带回归 (MA ± 2σ)
- rsi_revert: RSI 反转 (RSI<30 买, RSI>70 卖)

V1.0 改进: 改 backtrader / 自研事件驱动 + Walk-Forward 防过拟合
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Callable
from datetime import date, datetime
import json


# ============================================================
# 策略注册表
# ============================================================
STRATEGIES: Dict[str, Dict[str, Any]] = {
    "dual_ma_5_20": {
        "name": "双均线 (5/20)",
        "category": "trend",
        "params": {"short": 5, "long": 20},
        "signal_fn": "_signal_dual_ma",
        "description": "MA5 上穿 MA20 买入, 下穿卖出。经典趋势策略。",
    },
    "dual_ma_10_30": {
        "name": "双均线 (10/30)",
        "category": "trend",
        "params": {"short": 10, "long": 30},
        "signal_fn": "_signal_dual_ma",
        "description": "中线版双均线, MA10/MA30。",
    },
    "turtle_breakout": {
        "name": "海龟突破 (20日)",
        "category": "trend",
        "params": {"entry": 20, "exit": 10},
        "signal_fn": "_signal_turtle",
        "description": "突破 20 日高点买入, 跌破 10 日低点卖出。",
    },
    "bollinger_revert": {
        "name": "布林带回归 (20日, 2σ)",
        "category": "mean_reversion",
        "params": {"period": 20, "std": 2},
        "signal_fn": "_signal_bollinger",
        "description": "触及下轨买入, 触及上轨卖出。",
    },
    "rsi_revert": {
        "name": "RSI 反转 (14日)",
        "category": "mean_reversion",
        "params": {"buy": 30, "sell": 70, "period": 14},
        "signal_fn": "_signal_rsi",
        "description": "RSI<30 买入, RSI>70 卖出。",
    },
}


# ============================================================
# 信号生成函数
# 每个输入 df 含 close, high, low 列, 返回 signal 0/1 列
# ============================================================
def _signal_dual_ma(df: pd.DataFrame, short: int = 5, long: int = 20) -> pd.Series:
    """双均线: MA短 > MA长 = 持多"""
    ma_short = df["close"].rolling(short).mean()
    ma_long = df["close"].rolling(long).mean()
    return (ma_short > ma_long).astype(int).fillna(0)


def _signal_turtle(df: pd.DataFrame, entry: int = 20, exit: int = 10) -> pd.Series:
    """海龟突破: close > 20日最高 = 买入; close < 10日最低 = 卖出"""
    high_entry = df["high"].rolling(entry).max().shift(1)  # 昨日的 20 日最高
    low_exit = df["low"].rolling(exit).min().shift(1)     # 昨日的 10 日最低
    signal = pd.Series(0, index=df.index)
    signal[df["close"] > high_entry] = 1
    signal[df["close"] < low_exit] = 0
    return signal.fillna(0)


def _signal_bollinger(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.Series:
    """布林带: close < 下轨 = 买入; close > 上轨 = 卖出"""
    mid = df["close"].rolling(period).mean()
    sigma = df["close"].rolling(period).std()
    upper = mid + std * sigma
    lower = mid - std * sigma
    signal = pd.Series(0, index=df.index)
    signal[df["close"] < lower] = 1
    signal[df["close"] > upper] = 0
    return signal.fillna(0)


def _signal_rsi(df: pd.DataFrame, buy: int = 30, sell: int = 70, period: int = 14) -> pd.Series:
    """RSI: RSI < buy = 买入; RSI > sell = 卖出"""
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - 100 / (1 + rs)
    signal = pd.Series(0, index=df.index)
    signal[rsi < buy] = 1
    signal[rsi > sell] = 0
    return signal.fillna(0)


SIGNAL_FNS = {
    "_signal_dual_ma": _signal_dual_ma,
    "_signal_turtle": _signal_turtle,
    "_signal_bollinger": _signal_bollinger,
    "_signal_rsi": _signal_rsi,
}


# ============================================================
# 回测引擎
# ============================================================
class BacktestEngine:
    """多策略事件驱动回测引擎"""

    def __init__(
        self,
        initial_cash: float = 1_000_000.0,
        commission_rate: float = 0.0003,
        slippage: float = 0.001,
    ):
        self.initial_cash = initial_cash
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.data_dir = Path(__file__).resolve().parents[3] / "data" / "kline"

    def list_strategies(self) -> List[Dict[str, Any]]:
        return [
            {"id": sid, "name": s["name"], "category": s["category"],
             "description": s["description"], "params": s["params"]}
            for sid, s in STRATEGIES.items()
        ]

    def run(
        self,
        strategy_id: str,
        start_date,
        end_date,
        universe: List[str],
    ) -> Dict[str, Any]:
        """统一入口: 根据 strategy_id 派发"""
        if strategy_id not in STRATEGIES:
            return self._empty_result(f"未知策略: {strategy_id}")
        meta = STRATEGIES[strategy_id]
        signal_fn = SIGNAL_FNS[meta["signal_fn"]]
        params = meta["params"]
        return self._run_signal(signal_fn, params, start_date, end_date, universe, strategy_id)

    def run_dual_ma(
        self, start_date, end_date, universe: List[str], strategy_id: str = "dual_ma_5_20"
    ) -> Dict[str, Any]:
        """向后兼容"""
        return self.run(strategy_id, start_date, end_date, universe)

    def _run_signal(
        self,
        signal_fn: Callable,
        params: Dict[str, Any],
        start_date,
        end_date,
        universe: List[str],
        strategy_id: str,
    ) -> Dict[str, Any]:
        if not universe:
            return self._empty_result("股票池为空")

        # 加载所有股票日线
        stock_data: Dict[str, pd.DataFrame] = {}
        for code in universe:
            df = self._load_one(code)
            if df is not None and not df.empty:
                df = df[(df["trade_date"] >= pd.Timestamp(start_date)) &
                         (df["trade_date"] <= pd.Timestamp(end_date))].copy()
                if not df.empty:
                    stock_data[code] = df

        if not stock_data:
            return self._empty_result("股票池无有效数据,请先同步 Tushare")

        # 取主标的 (MVP 单标的)
        main_code = list(stock_data.keys())[0]
        df = stock_data[main_code].sort_values("trade_date").reset_index(drop=True)

        # 计算信号
        df["signal"] = signal_fn(df, **params).astype(int)
        df["position"] = df["signal"].shift(1).fillna(0)  # T+1 撮合

        # 收益
        df["ret"] = df["close"].pct_change().fillna(0)
        df["strategy_ret"] = df["position"] * df["ret"]

        # 累计净值
        df["nav"] = (1 + df["strategy_ret"]).cumprod() * self.initial_cash
        df["benchmark_nav"] = (1 + df["ret"]).cumprod() * self.initial_cash

        # 交易记录
        trades = self._extract_trades(df, main_code)
        # 绩效指标
        metrics = self._calc_metrics(df)

        return {
            "main_code": main_code,
            "strategy_id": strategy_id,
            "params": params,
            "trade_count": len(trades),
            "trades": trades[:50],
            "equity_curve": [
                {
                    "date": r["trade_date"].strftime("%Y-%m-%d"),
                    "nav": round(float(r["nav"]), 2),
                    "benchmark": round(float(r["benchmark_nav"]), 2),
                    "position": int(r["position"]),
                }
                for _, r in df.iterrows()
            ][::5],  # 抽样
            "metrics": metrics,
        }

    def _load_one(self, ts_code: str) -> pd.DataFrame | None:
        file = self.data_dir / f"{ts_code}_1d.csv"
        if not file.exists():
            return None
        try:
            return pd.read_csv(file, parse_dates=["trade_date"])
        except Exception:
            return None

    def _extract_trades(self, df: pd.DataFrame, code: str) -> List[dict]:
        trades = []
        prev = 0
        for _, r in df.iterrows():
            cur = int(r["position"])
            if cur != prev and cur == 1:
                trades.append({
                    "date": r["trade_date"].strftime("%Y-%m-%d"),
                    "code": code,
                    "side": "buy",
                    "price": round(float(r["close"]) * (1 + self.slippage), 2),
                })
            elif cur != prev and cur == 0:
                trades.append({
                    "date": r["trade_date"].strftime("%Y-%m-%d"),
                    "code": code,
                    "side": "sell",
                    "price": round(float(r["close"]) * (1 - self.slippage), 2),
                })
            prev = cur
        return trades

    def _calc_metrics(self, df: pd.DataFrame) -> dict:
        total_ret = (df["nav"].iloc[-1] / self.initial_cash - 1) if len(df) else 0
        bench_ret = (df["benchmark_nav"].iloc[-1] / self.initial_cash - 1) if len(df) else 0
        n_days = len(df)
        annual_ret = (1 + total_ret) ** (252 / n_days) - 1 if n_days > 0 else 0
        daily_ret = df["strategy_ret"]
        sharpe = (daily_ret.mean() / (daily_ret.std() + 1e-9)) * (252 ** 0.5) if len(daily_ret) > 1 else 0
        nav = df["nav"]
        peak = nav.cummax()
        dd = (nav - peak) / peak
        max_dd = float(dd.min()) if len(dd) else 0
        return {
            "total_return": round(float(total_ret), 4),
            "annual_return": round(float(annual_ret), 4),
            "benchmark_return": round(float(bench_ret), 4),
            "alpha": round(float(annual_ret - bench_ret), 4),
            "sharpe_ratio": round(float(sharpe), 2),
            "max_drawdown": round(float(max_dd), 4),
            "trade_days": n_days,
            "trade_count": int((df["position"].diff().fillna(0) != 0).sum() // 2),
        }

    def _empty_result(self, reason: str) -> dict:
        return {
            "main_code": None,
            "strategy_id": None,
            "params": {},
            "trade_count": 0,
            "trades": [],
            "equity_curve": [],
            "metrics": {
                "total_return": 0, "annual_return": 0, "benchmark_return": 0,
                "alpha": 0, "sharpe_ratio": 0, "max_drawdown": 0,
                "trade_days": 0, "trade_count": 0, "win_rate": 0,
            },
            "_warning": reason,
        }
