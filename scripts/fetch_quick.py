"""
快速验证: 拉股票列表 + 前 50 只热门股 5 年 K 线
预计 3-5 分钟
"""
import os
import sys
import json
import time
from pathlib import Path

TOKEN = os.environ.get("TUSHARE_TOKEN", "02345d100a928575ac032c8e4fc0142896859cf15276323951f90c20")

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
KLINE_DIR = DATA_DIR / "kline"
DATA_DIR.mkdir(parents=True, exist_ok=True)
KLINE_DIR.mkdir(parents=True, exist_ok=True)

import tushare as ts
import pandas as pd

ts.set_token(TOKEN)
pro = ts.pro_api()
print(f"[OK] tushare {ts.__version__}, token = ***{TOKEN[-6:]}")

# 1. 拉股票列表 (限速 1次/分钟, 加 retry)
print("\n[1/3] 拉股票基础信息...")
for retry in range(5):
    try:
        df = pro.stock_basic(list_status="L", fields="ts_code,symbol,name,area,industry,market,list_date")
        df_a = df[df["market"].isin(["SZ", "SH"])].copy()
        print(f"  全市场: {len(df)} 只, A 股: {len(df_a)} 只")
        df_a.to_json(DATA_DIR / "stocks.json", orient="records", force_ascii=False)
        print(f"  -> data/stocks.json")
        break
    except Exception as e:
        if "频率" in str(e) or "limit" in str(e).lower():
            print(f"  [限速] retry {retry+1}/5, 等待 65s...")
            time.sleep(65)
        else:
            raise
else:
    print("  [FAIL] 5 次重试都失败")
    sys.exit(1)

# 2. 选 50 只热门 (按总市值 Top 50)
print("\n[2/3] 拉日基础指标 (取市值 Top 50)...")
for retry in range(5):
    try:
        df_basic = pro.daily_basic(
            trade_date="20260618",  # 最近交易日
            fields="ts_code,total_mv,circ_mv,pe,pb,turnover_rate",
            limit=5000,
        )
        df_basic = df_basic.sort_values("total_mv", ascending=False).head(50)
        print(f"  Top 50 总市值股 (总市值单位: 万元)")
        df_basic.to_json(DATA_DIR / "top_stocks.json", orient="records", force_ascii=False)
        break
    except Exception as e:
        if "频率" in str(e) or "limit" in str(e).lower():
            print(f"  [限速] retry {retry+1}/5, 等待 65s...")
            time.sleep(65)
        else:
            raise
else:
    print("  [FAIL] 5 次重试都失败")
    sys.exit(1)

# 3. 拉这 50 只 5 年日 K 线
print(f"\n[3/3] 拉 50 只 × 5 年日 K 线 (20200101 ~ 20260619)...")
success = 0
failed = 0
total = len(df_basic)
for idx, row in df_basic.iterrows():
    code = row["ts_code"]
    out = KLINE_DIR / f"{code}_1d.csv"
    try:
        df_d = pro.daily(
            ts_code=code,
            start_date="20200101",
            end_date="20260619",
        )
        if df_d is None or df_d.empty:
            failed += 1
            continue
        df_d = df_d.sort_values("trade_date")
        df_d.to_csv(out, index=False, encoding="utf-8")
        success += 1
        if success % 10 == 0:
            print(f"  [{success}/{total}] {code}: {len(df_d)} 行, "
                  f"{df_d.iloc[0]['trade_date']} ~ {df_d.iloc[-1]['trade_date']}, "
                  f"收 {df_d.iloc[-1]['close']}")
        time.sleep(0.35)  # 限速 200 req/min ≈ 3 req/s
    except Exception as e:
        err = str(e)
        if "每分钟" in err or "limit" in err.lower() or "429" in err:
            print(f"  [限速] sleep 60s")
            time.sleep(60)
            # 重试
            try:
                df_d = pro.daily(ts_code=code, start_date="20200101", end_date="20260619")
                if df_d is not None and not df_d.empty:
                    df_d.sort_values("trade_date").to_csv(out, index=False, encoding="utf-8")
                    success += 1
            except:
                failed += 1
        else:
            failed += 1
            if failed < 3:
                print(f"  [ERR] {code}: {err}")

print(f"\n[DONE] 成功 {success} / 失败 {failed}")
print(f"  K 线文件: {len(list(KLINE_DIR.glob('*_1d.csv')))} 个")
