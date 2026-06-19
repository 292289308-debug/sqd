"""
拉 Top 100 总市值股 + 5 年日 K 线
- daily_basic 拉 Top 100 (1次/分钟限速, 重试)
- 逐个 daily 拉 K 线 (200次/分钟)
"""
import os
import sys
import time
import json
from pathlib import Path

TOKEN = os.environ.get("TUSHARE_TOKEN", "02345d100a928575ac032c8e4fc0142896859cf15276323951f90c20")
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
KLINE_DIR = DATA_DIR / "kline"
KLINE_DIR.mkdir(parents=True, exist_ok=True)

import tushare as ts
import pandas as pd

ts.set_token(TOKEN)
pro = ts.pro_api()
print(f"[OK] tushare, token = ***{TOKEN[-6:]}")

# 1. 拉 Top 100 (用 daily_basic 拿到总市值排序, 限速 1次/分钟)
print("\n[1/2] 拉 Top 100 总市值股 (daily_basic)...")
for retry in range(5):
    try:
        df = pro.daily_basic(
            trade_date="20260618",
            fields="ts_code,total_mv,circ_mv,pe,pb,turnover_rate,name,industry",
            limit=5000,
        )
        df = df.sort_values("total_mv", ascending=False).head(100)
        print(f"  Top 100 总市值股 OK")
        df.to_json(DATA_DIR / "top100.json", orient="records", force_ascii=False)
        break
    except Exception as e:
        if "频率" in str(e) or "limit" in str(e).lower():
            print(f"  [限速] retry {retry+1}/5, sleep 70s...")
            time.sleep(70)
        else:
            raise
else:
    print("  [FAIL] 失败")
    sys.exit(1)

# 2. 拉每只 5 年 K 线
codes = df["ts_code"].tolist()
print(f"\n[2/2] 拉 {len(codes)} 只 × 5 年 K 线...")
print(f"  daily 接口限速 200/min, 加 sleep 0.35s 防触发\n")

success = 0
failed = 0
for i, code in enumerate(codes, 1):
    out = KLINE_DIR / f"{code}_1d.csv"
    if out.exists() and out.stat().st_size > 50000:  # 已有真实数据 (>5年=1200+行, 4K+)
        success += 1
        if i % 20 == 0:
            print(f"  [{i}/{len(codes)}] 跳过 (已有)")
        continue
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
            print(f"  [{i}/{len(codes)}] {code}: {len(df_d)} 行, "
                  f"最近 {df_d.iloc[-1]['trade_date']} 收 {df_d.iloc[-1]['close']}")
        time.sleep(0.35)
    except Exception as e:
        err = str(e)
        if "频率" in err or "limit" in err.lower() or "429" in err:
            print(f"  [{i}/{len(codes)}] {code}: [限速] sleep 60s")
            time.sleep(60)
            try:
                df_d = pro.daily(ts_code=code, start_date="20200101", end_date="20260619")
                if df_d is not None and not df_d.empty:
                    df_d.sort_values("trade_date").to_csv(out, index=False, encoding="utf-8")
                    success += 1
            except:
                failed += 1
        else:
            failed += 1

print(f"\n[DONE] 成功 {success} / 失败 {failed}")
print(f"  K 线文件总数: {len(list(KLINE_DIR.glob('*_1d.csv')))}")
