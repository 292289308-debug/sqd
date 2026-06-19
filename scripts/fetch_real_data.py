"""
拉真实 A 股数据 (Tushare Pro)
- 拉股票基础信息 (stock_basic) ~5500 只
- 拉日 K 线 (daily) - 默认 2020-01-01 至今
- 存到 data/stocks.json + data/kline/{ts_code}_1d.csv

用法:
    $env:TUSHARE_TOKEN = "your_token"
    python scripts/fetch_real_data.py
"""
import os
import sys
import json
import time
from pathlib import Path

# 1. 拿 token
TOKEN = os.environ.get("TUSHARE_TOKEN")
if not TOKEN:
    print("[ERR] 请设置环境变量 TUSHARE_TOKEN")
    sys.exit(1)

# 2. 路径
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
KLINE_DIR = DATA_DIR / "kline"
DATA_DIR.mkdir(parents=True, exist_ok=True)
KLINE_DIR.mkdir(parents=True, exist_ok=True)

# 3. import tushare
import tushare as ts
import pandas as pd

ts.set_token(TOKEN)
pro = ts.pro_api()

print(f"[OK] tushare {ts.__version__} loaded, token = ***{TOKEN[-6:]}")


# 4. 拉股票基础信息
def fetch_stock_basic():
    print("\n[1/3] 拉股票基础信息 (stock_basic)...")
    df = pro.stock_basic(
        list_status="L",
        fields="ts_code,symbol,name,industry,list_date,market,exchange",
    )
    print(f"  共 {len(df)} 只股票 (含 A 股 + 港股)")
    # 只保留 A 股
    df_a = df[df["market"].isin(["SZ", "SH"])].copy()
    print(f"  A 股: {len(df_a)} 只")
    out = DATA_DIR / "stocks.json"
    df_a.to_json(out, orient="records", force_ascii=False)
    print(f"  保存到 {out}")
    return df_a


# 5. 拉日 K 线
def fetch_daily_kline(stocks_df, start_date="20200101", end_date=None):
    if end_date is None:
        end_date = pd.Timestamp.now().strftime("%Y%m%d")
    print(f"\n[2/3] 拉日 K 线 ({start_date} ~ {end_date})...")
    # 优先拉主板/创业板，避免一次拉太多
    # 一次只拉一只，限速防 429
    success = 0
    failed = 0
    skipped = 0
    for idx, row in stocks_df.iterrows():
        code = row["ts_code"]
        out = KLINE_DIR / f"{code}_1d.csv"
        if out.exists() and out.stat().st_size > 200:
            # 已有数据, 跳过
            skipped += 1
            continue
        try:
            df = pro.daily(
                ts_code=code,
                start_date=start_date,
                end_date=end_date,
            )
            if df is None or df.empty:
                failed += 1
                continue
            df = df.sort_values("trade_date")
            df.to_csv(out, index=False, encoding="utf-8")
            success += 1
            if success % 50 == 0:
                print(f"  [{success}/{len(stocks_df)}] {code} ({row['name']}): {len(df)} 行, 最近 {df.iloc[-1]['trade_date']}")
        except Exception as e:
            err = str(e)
            if "每分钟" in err or "limit" in err.lower() or "429" in err:
                print(f"  [限速] 等待 60s 后重试...")
                time.sleep(60)
            else:
                failed += 1
                if failed < 5:
                    print(f"  [ERR] {code}: {err}")
    print(f"  完成: 成功 {success} / 失败 {failed} / 跳过 {skipped} / 总 {len(stocks_df)}")


# 6. 拉基础指标 (PE/PB/换手率)
def fetch_daily_basic(stocks_df, start_date="20200101", end_date=None):
    if end_date is None:
        end_date = pd.Timestamp.now().strftime("%Y%m%d")
    print(f"\n[3/3] 拉日基础指标 (daily_basic)...")
    success = 0
    failed = 0
    for idx, row in stocks_df.iterrows():
        code = row["ts_code"]
        out = KLINE_DIR / f"{code}_1d_basic.csv"
        if out.exists() and out.stat().st_size > 200:
            continue
        try:
            df = pro.daily_basic(
                ts_code=code,
                start_date=start_date,
                end_date=end_date,
                fields="ts_code,trade_date,turnover_rate,pe,pb,total_mv,circ_mv",
            )
            if df is None or df.empty:
                failed += 1
                continue
            df = df.sort_values("trade_date")
            df.to_csv(out, index=False, encoding="utf-8")
            success += 1
        except Exception as e:
            err = str(e)
            if "每分钟" in err or "limit" in err.lower() or "429" in err:
                print(f"  [限速] 等待 60s 后重试...")
                time.sleep(60)
            else:
                failed += 1
    print(f"  完成: 成功 {success} / 失败 {failed}")


if __name__ == "__main__":
    print(f"\n=== 拉真实 A 股数据 ===")
    print(f"日期范围: 2020-01-01 ~ 至今")
    print(f"目标: 全 A 股 ({5000}+ 只) + 5 年日 K 线 + 基础指标")
    print(f"预计时间: 30~60 分钟 (Tushare 限速 200 req/min)\n")

    # 1. 股票列表
    stocks = fetch_stock_basic()

    # 2. 拉日 K 线
    fetch_daily_kline(stocks)

    # 3. 拉日基础指标
    fetch_daily_basic(stocks)

    print("\n[DONE] 全部完成!")
    print(f"  股票列表: data/stocks.json")
    print(f"  K 线 CSV: data/kline/  ({len(list(KLINE_DIR.glob('*_1d.csv')))} 个文件)")
