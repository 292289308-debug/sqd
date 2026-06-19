"""
回测引擎 MVP - 双均线策略
事件驱动简化版: 每日判断金叉死叉 → 调仓

V1.0 改进: 改 backtrader / 自研事件驱动 + 多策略并发
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from datetime import date, datetime
import json


class BacktestEngine:
    """MVP 双均线回测引擎"""

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

    def run_dual_ma(
        self,
        start_date,
        end_date,
        universe: List[str],
        strategy_id: str = "dual_ma_5_20",
    ) -> Dict[str, Any]:
        """
        双均线策略 (默认 5/20):
        - 金叉 (MA5 上穿 MA20): 满仓买入
        - 死叉 (MA5 下穿 MA20): 清仓
        - 等权分配到 universe 里所有股票
        """
        # MVP: 只对第一只股票做回测 (单标的演示)
        # 真实版: 多标的并行 + 调仓逻辑
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
                    df["ma5"] = df["close"].rolling(5).mean()
                    df["ma20"] = df["close"].rolling(20).mean()
                    stock_data[code] = df

        if not stock_data:
            return self._empty_result("股票池无有效数据,请先同步 Tushare")

        # 取主标的 (MVP 单标的)
        main_code = list(stock_data.keys())[0]
        df = stock_data[main_code].sort_values("trade_date").reset_index(drop=True)

        # 信号: MA5 > MA20 持多, 反之空仓
        df["signal"] = (df["ma5"] > df["ma20"]).astype(int)
        df["position"] = df["signal"].shift(1).fillna(0)  # T+1 撮合

        # 收益计算
        df["ret"] = df["close"].pct_change().fillna(0)
        df["strategy_ret"] = df["position"] * df["ret"]

        # 累计净值
        df["nav"] = (1 + df["strategy_ret"]).cumprod() * self.initial_cash
        df["benchmark_nav"] = (1 + df["ret"]).cumprod() * self.initial_cash

        # 交易记录
        trades = self._extract_trades(df, main_code)

        # 绩效指标
        metrics = self._calc_metrics(df, trades)

        return {
            "main_code": main_code,
            "trade_count": len(trades),
            "trades": trades[:50],  # 最多返回 50 笔
            "equity_curve": [
                {
                    "date": r["trade_date"].strftime("%Y-%m-%d"),
                    "nav": round(float(r["nav"]), 2),
                    "benchmark": round(float(r["benchmark_nav"]), 2),
                    "position": int(r["position"]),
                }
                for _, r in df.iterrows()
            ][::5],  # 抽样返回, 避免过大
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
        """提取交易记录 (信号变化时记录)"""
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

    def _calc_metrics(self, df: pd.DataFrame, trades: List[dict]) -> dict:
        """计算绩效指标"""
        total_ret = (df["nav"].iloc[-1] / self.initial_cash - 1) if len(df) else 0
        bench_ret = (df["benchmark_nav"].iloc[-1] / self.initial_cash - 1) if len(df) else 0
        n_days = len(df)
        annual_ret = (1 + total_ret) ** (252 / n_days) - 1 if n_days > 0 else 0
        daily_ret = df["strategy_ret"]
        sharpe = (daily_ret.mean() / (daily_ret.std() + 1e-9)) * (252 ** 0.5) if len(daily_ret) > 1 else 0
        # 最大回撤
        nav = df["nav"]
        peak = nav.cummax()
        dd = (nav - peak) / peak
        max_dd = float(dd.min()) if len(dd) else 0
        # 胜率
        sell_trades = [t for t in trades if t["side"] == "sell"]
        win_rate = 0  # MVP 简化, 需配对 buy-sell 计算
        return {
            "total_return": round(float(total_ret), 4),
            "annual_return": round(float(annual_ret), 4),
            "benchmark_return": round(float(bench_ret), 4),
            "alpha": round(float(annual_ret - bench_ret), 4),
            "sharpe_ratio": round(float(sharpe), 2),
            "max_drawdown": round(float(max_dd), 4),
            "trade_days": n_days,
            "trade_count": len(trades),
            "win_rate": win_rate,
        }

    def _empty_result(self, reason: str) -> dict:
        return {
            "main_code": None,
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
