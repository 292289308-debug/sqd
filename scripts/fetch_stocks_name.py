"""
拉 Top 100 股票 (带 name + industry) 存到 stocks.json
"""
import os
import time
import json
from pathlib import Path

TOKEN = os.environ.get("TUSHARE_TOKEN", "02345d100a928575ac032c8e4fc0142896859cf15276323951f90c20")
ROOT = Path(__file__).parent.parent

import tushare as ts
import pandas as pd

ts.set_token(TOKEN)
pro = ts.pro_api()
print(f"token = ***{TOKEN[-6:]}")

for retry in range(5):
    try:
        df = pro.daily_basic(
            trade_date="20260618",
            fields="ts_code,name,industry,area,total_mv,circ_mv,pe,pb,turnover_rate",
            limit=5000,
        )
        df = df.sort_values("total_mv", ascending=False).head(100)
        # 补字段
        df["market"] = df["ts_code"].apply(lambda c: c.split(".")[-1] if "." in c else "")
        df["symbol"] = df["ts_code"].apply(lambda c: c.split(".")[0] if "." in c else "")
        df["list_date"] = ""
        df.to_json(ROOT / "data" / "stocks.json", orient="records", force_ascii=False)
        n_with_name = df["name"].notna().sum()
        print(f"[OK] stocks.json: {len(df)} 只, {n_with_name} 有 name")
        print(df[["ts_code", "name", "industry", "total_mv"]].head(10).to_string(index=False))
        break
    except Exception as e:
        if "频率" in str(e) or "limit" in str(e).lower():
            print(f"[限速] retry {retry+1}/5, sleep 90s...")
            time.sleep(90)
        else:
            print(f"[ERR] {e}")
            raise
else:
    print("FAIL")
