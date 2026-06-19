"""
初始化 demo 数据 (无 Tushare token 时也能跑)
"""
import sys
import json
from pathlib import Path

# 把 backend 加到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.data_fetcher import fetch_stock_basic, fetch_daily_kline  # noqa: E402

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def main():
    # 1. 股票基础信息
    df = fetch_stock_basic()
    stocks = df.to_dict("records")
    (DATA_DIR / "stocks_demo.json").write_text(
        json.dumps(stocks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 写入 {len(stocks)} 只股票")

    # 2. 前 10 只的 K 线
    for s in stocks[:10]:
        code = s["ts_code"]
        df_k = fetch_daily_kline(code, "20250101", "20260619")
        if not df_k.empty:
            last = df_k.iloc[-1]
            print(f"  {code} ({s['name']}): {len(df_k)} 行, "
                  f"最近 {last['trade_date']} 收 {last['close']}")

    # 3. 自选股 demo
    watchlist = {
        "groups": [
            {
                "name": "银行",
                "items": [
                    {"ts_code": "600036.SH", "name": "招商银行"},
                    {"ts_code": "601398.SH", "name": "工商银行"},
                ],
            },
            {
                "name": "白酒",
                "items": [
                    {"ts_code": "600519.SH", "name": "贵州茅台"},
                    {"ts_code": "000858.SZ", "name": "五粮液"},
                ],
            },
        ]
    }
    (DATA_DIR / "watchlist_demo.json").write_text(
        json.dumps(watchlist, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 写入自选股 demo")

    # 4. 策略模板
    strategies = [
        {
            "id": "dual_ma_5_20",
            "name": "双均线 (5/20)",
            "category": "trend",
            "description": "MA5 上穿 MA20 买入, 下穿卖出。经典趋势策略。",
            "params": {"short": 5, "long": 20},
            "code": "# 见 app/services/backtest_engine.py run_dual_ma",
        },
        {
            "id": "dual_ma_10_30",
            "name": "双均线 (10/30)",
            "category": "trend",
            "description": "中线版双均线, MA10/MA30。",
            "params": {"short": 10, "long": 30},
            "code": "TBD",
        },
        {
            "id": "turtle_breakout",
            "name": "海龟突破 (20日)",
            "category": "trend",
            "description": "突破 20 日高点买入, 跌破 10 日低点卖出。",
            "params": {"entry": 20, "exit": 10},
            "code": "TBD",
        },
        {
            "id": "bollinger_revert",
            "name": "布林带回归",
            "category": "mean_reversion",
            "description": "触及下轨买入, 触及上轨卖出。",
            "params": {"period": 20, "std": 2},
            "code": "TBD",
        },
        {
            "id": "rsi_revert",
            "name": "RSI 反转",
            "category": "mean_reversion",
            "description": "RSI<30 买入, RSI>70 卖出。",
            "params": {"buy": 30, "sell": 70, "period": 14},
            "code": "TBD",
        },
        {
            "id": "momentum_12_1",
            "name": "12-1 动量",
            "category": "factor",
            "description": "买入过去 12 月涨跌幅最高, 跳过最近 1 月 (避免反转)。",
            "params": {"lookback": 12, "skip": 1},
            "code": "TBD",
        },
    ]
    (DATA_DIR / "strategies_demo.json").write_text(
        json.dumps(strategies, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] 写入 {len(strategies)} 个策略模板")


if __name__ == "__main__":
    main()
