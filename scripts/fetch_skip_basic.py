"""
绕过 stock_basic 限速: 用 demo 的 10 只股票做种子, 拉它们的真实 5 年 K 线
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

# 用现有 demo 的 10 只股票做种子
SEED_CODES = [
    "000001.SZ", "000002.SZ", "000333.SZ", "000858.SZ",
    "600000.SH", "600036.SH", "600519.SH", "600887.SH",
    "601318.SH", "601398.SH",
]
# 加几个大盘股, 让回测更有看头
SEED_CODES += [
    "600276.SH",  # 恒瑞医药
    "000651.SZ",  # 格力电器
    "002594.SZ",  # 比亚迪
    "300750.SZ",  # 宁德时代
    "601012.SH",  # 隆基绿能
    "002415.SZ",  # 海康威视
    "600030.SH",  # 中信证券
    "601166.SH",  # 兴业银行
    "600028.SH",  # 中国石化
    "601857.SH",  # 中国石油
]

print(f"\n[1/1] 拉 {len(SEED_CODES)} 只 5 年 K 线...")
print(f"日期: 2020-01-01 ~ 2026-06-19")
print(f"限制: 200 req/min = 3 req/s, 加 sleep 0.4s 防触发\n")

success = 0
failed = 0
for i, code in enumerate(SEED_CODES, 1):
    out = KLINE_DIR / f"{code}_1d.csv"
    # 删除 demo 数据
    if out.exists() and out.stat().st_size < 5000:  # demo 数据只 60 行, 真实数据会 5年~1200行
        out.unlink()
    try:
        df = pro.daily(
            ts_code=code,
            start_date="20200101",
            end_date="20260619",
        )
        if df is None or df.empty:
            failed += 1
            print(f"  [{i}/{len(SEED_CODES)}] {code}: 空数据")
            continue
        df = df.sort_values("trade_date")
        df.to_csv(out, index=False, encoding="utf-8")
        success += 1
        if success % 5 == 0 or i == len(SEED_CODES):
            last_date = df.iloc[-1]["trade_date"]
            last_close = df.iloc[-1]["close"]
            print(f"  [{i}/{len(SEED_CODES)}] {code}: {len(df)} 行, "
                  f"{df.iloc[0]['trade_date']} ~ {last_date}, 收 {last_close}")
        time.sleep(0.4)  # 防限速
    except Exception as e:
        err = str(e)
        if "频率" in err or "limit" in err.lower() or "429" in err:
            print(f"  [{i}/{len(SEED_CODES)}] {code}: [限速] sleep 60s")
            time.sleep(60)
            # 重试
            try:
                df = pro.daily(ts_code=code, start_date="20200101", end_date="20260619")
                if df is not None and not df.empty:
                    df.sort_values("trade_date").to_csv(out, index=False, encoding="utf-8")
                    success += 1
            except:
                failed += 1
        else:
            failed += 1
            if failed < 3:
                print(f"  [ERR] {code}: {err}")

print(f"\n[DONE] 成功 {success} / 失败 {failed}")
print(f"  K 线文件: {len(list(KLINE_DIR.glob('*_1d.csv')))} 个")
