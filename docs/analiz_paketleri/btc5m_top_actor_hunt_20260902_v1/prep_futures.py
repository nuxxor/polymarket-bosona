#!/usr/bin/env python3
import duckdb, zipfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = HERE.parents[2] / "data/binance_vision/futures_um/trades/BTCUSDT/daily"
TMP = Path("/tmp/claude-1000/-home-taygun-Masa-st--polymarket/361c82d8-4092-4426-9c1b-657e6613e879/scratchpad/binance_fut_csv"); TMP.mkdir(parents=True, exist_ok=True)
days = [f"2026-08-{d:02d}" for d in range(13, 32)] + ["2026-09-01"]
csvs = []
for d in days:
    z = SRC / f"BTCUSDT-trades-{d}.zip"
    if not z.exists(): print("missing", d); continue
    out = TMP / f"{d}.csv"
    if not out.exists():
        with zipfile.ZipFile(z) as zf: out.write_bytes(zf.read(zf.namelist()[0]))
    csvs.append(str(out))
con = duckdb.connect(); con.execute("PRAGMA threads=4"); con.execute("PRAGMA memory_limit='16GB'")
# futures trades csv: id, price, qty, quote_qty, time(ms or us), is_buyer_maker (header row present)
con.execute(f"""copy (select (ts//1000) s, arg_max(px, ts) last_px, sum(case when bm then -qq else qq end) signed_usd, sum(qq) usd
  from (select column1::double px, column3::double qq, (case when column4::bigint > 1000000000000000 then column4::bigint // 1000 else column4::bigint end) ts, column5::boolean bm
        from read_csv({csvs!r}, header=true, columns={{'column0':'BIGINT','column1':'DOUBLE','column2':'DOUBLE','column3':'DOUBLE','column4':'BIGINT','column5':'BOOLEAN'}}))
  group by 1 order by 1) to '{HERE}/BINANCE_FUT_1S.parquet' (format parquet, compression zstd)""")
print(con.execute(f"select count(*), min(s), max(s) from read_parquet('{HERE}/BINANCE_FUT_1S.parquet')").fetchone())
