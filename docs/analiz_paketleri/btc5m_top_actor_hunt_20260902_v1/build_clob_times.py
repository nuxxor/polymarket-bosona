#!/usr/bin/env python3
"""CLOB match clock per (start_ts, tx_hash) from Telonex `trades` (trade_id == tx_hash)."""
import sqlite3
from pathlib import Path
import duckdb
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
con_s = sqlite3.connect(HERE / "TELONEX_DOWNLOAD_STATE.sqlite3")
files = [r[0] for r in con_s.execute("select path from tasks where channel='trades' and status in ('downloaded','shared') and rows>0")]
print("trade files", len(files))
con = duckdb.connect(); con.execute("PRAGMA memory_limit='16GB'"); con.execute("PRAGMA threads=6"); con.execute("PRAGMA preserve_insertion_order=false")
con.execute(f"""copy (
  select cast(regexp_extract(slug, '(\\d+)$', 1) as bigint) start_ts, trade_id as tx_hash,
         min(timestamp_us) clob_ts, min(local_timestamp_us) local_ts, count(*) n_rows,
         arg_min(cast(price as double), timestamp_us) clob_price, sum(cast(size as double)) clob_size, arg_min(side, timestamp_us) clob_side, arg_min(outcome, timestamp_us) clob_outcome
  from read_parquet({files!r}, union_by_name=true) group by 1,2
) to '{HERE}/CLOB_TIMES.parquet' (format parquet, compression zstd)""")
print(con.execute(f"select count(*) n, count(distinct start_ts) mkts from read_parquet('{HERE}/CLOB_TIMES.parquet')").fetchone())
# coverage of fills
print(con.execute(f"""select count(*) fills, sum((c.clob_ts is not null)::int) matched, quantile_cont((f.ts - c.clob_ts)/1e6, [0.05,0.5,0.95]) lag_q
  from read_parquet('{HERE}/FILL_PARTY_LEDGER/taker.parquet') f left join read_parquet('{HERE}/CLOB_TIMES.parquet') c using (start_ts, tx_hash)""").fetchone())
