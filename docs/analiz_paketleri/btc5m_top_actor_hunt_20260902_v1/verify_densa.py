#!/usr/bin/env python3
"""Reconcile our ledger against the independent Densa audit (data/analysis/densa_twap60_actor_audit_20260828_v1).
Audit (public cash-flow, 100% taker BUY-only actor): post-Aug14 to freeze 2026-08-28 20:30Z:
  709 trades / 498 markets / fee-inclusive cost $15,068.75 / fee-net PnL +$2,895.08 / 9 active days."""
import duckdb
from pathlib import Path
HERE = Path(__file__).resolve().parent
W = '0x10bc0d95f8296023c8acf6faa42d6fe0e8c176be'
con = duckdb.connect()
print(con.execute(f"""select count(*) n_mkts, sum(n_fills) n_fills, sum(n_taker) n_taker, sum(n_maker) n_maker,
  round(sum(buy_notional)+sum(fee),2) cost_fee_incl, round(sum(sell_notional),2) sells, round(sum(pnl),2) pnl, round(sum(fee),2) fee,
  count(distinct market_date) n_days
  from read_parquet('{HERE}/WALLET_MARKET_LEDGER.parquet')
  where wallet='{W}' and resolved and start_ts >= 1786665600 and start_ts < 1787949000""").fetchdf().to_string())
print(con.execute(f"""select market_date, count(*) n, round(sum(pnl),2) pnl from read_parquet('{HERE}/WALLET_MARKET_LEDGER.parquet')
  where wallet='{W}' and resolved and start_ts >= 1786665600 and start_ts < 1787949000 group by 1 order by 1""").fetchdf().to_string())
