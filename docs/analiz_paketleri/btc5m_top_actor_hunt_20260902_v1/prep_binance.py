#!/usr/bin/env python3
"""Binance spot BTCUSDT aggTrades -> 100ms last-price series (UTC), 2026-08-13..2026-09-01."""
import duckdb, glob, zipfile, io, os
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = HERE.parents[2] / "data/binance_vision/spot/aggTrades/BTCUSDT/daily"
TMP = Path("/tmp/claude-1000/-home-taygun-Masa-st--polymarket/361c82d8-4092-4426-9c1b-657e6613e879/scratchpad/binance_csv")
TMP.mkdir(parents=True, exist_ok=True)
days = [f"2026-08-{d:02d}" for d in range(13, 32)] + ["2026-09-01"]
csvs = []
for d in days:
    z = SRC / f"BTCUSDT-aggTrades-{d}.zip"
    if not z.exists():
        print("missing", d); continue
    out = TMP / f"{d}.csv"
    if not out.exists():
        with zipfile.ZipFile(z) as zf:
            name = zf.namelist()[0]
            out.write_bytes(zf.read(name))
    csvs.append(str(out))
con = duckdb.connect(); con.execute("PRAGMA threads=4"); con.execute("PRAGMA memory_limit='12GB'")
con.execute(f"""copy (
  select bin_ms, arg_max(price, ts_ms) as last_px, min(price) lo, max(price) hi, sum(qty) vol, count(*) n
  from (select column1::double price, column2::double qty, (case when column5::bigint > 1000000000000000 then column5::bigint // 1000 else column5::bigint end) ts_ms, (case when column5::bigint > 1000000000000000 then column5::bigint // 1000 else column5::bigint end // 100)*100 as bin_ms
        from read_csv({csvs!r}, header=false, columns={{'column0':'BIGINT','column1':'DOUBLE','column2':'DOUBLE','column3':'BIGINT','column4':'BIGINT','column5':'BIGINT','column6':'BOOLEAN','column7':'BOOLEAN'}}))
  group by 1 order by 1) to '{HERE}/BINANCE_SPOT_100MS.parquet' (format parquet, compression zstd)""")
print(con.execute(f"select count(*), min(bin_ms), max(bin_ms) from read_parquet('{HERE}/BINANCE_SPOT_100MS.parquet')").fetchone())
