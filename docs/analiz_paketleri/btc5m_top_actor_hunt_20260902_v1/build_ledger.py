#!/usr/bin/env python3
"""Exact cash-flow ledger for every wallet in Polymarket btc-updown-5m, 2026-08-14..2026-09-02 (memory-bounded).

Accounting (verified on sibling files: mirrored rows carry price' = 1 - price, same amount/fee):
  p_m = price if not mirrored else 1 - price          -> price of maker_asset_id
  maker: trades `amount` of maker_asset_id at p_m, fee 0
  taker: trades `amount` of taker_asset_id at (p_m if taker_asset_id == maker_asset_id else 1 - p_m), pays taker_fee (USDC)
  cash = -shares*price (buy) / +shares*price (sell) - fee
  payout at resolution = net shares of winning asset x $1 (split/merge are $1-neutral, so this is exact)
Invariant: per market, sum of all wallets' pnl == -sum(taker_fee).
Market key = start_ts (slug timestamp, unique per market). outcome_idx 0=Up, 1=Down.
"""
from __future__ import annotations
import shutil, sqlite3
from pathlib import Path
import duckdb

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CATALOG = REPO / "datasets/polymarket_markets.parquet"
STATE = HERE / "TELONEX_DOWNLOAD_STATE.sqlite3"
PARTY = HERE / "FILL_PARTY_LEDGER"
TMP = Path("/tmp/claude-1000/-home-taygun-Masa-st--polymarket/361c82d8-4092-4426-9c1b-657e6613e879/scratchpad/duck_tmp")


def main() -> None:
    con_s = sqlite3.connect(STATE)
    files = [r[0] for r in con_s.execute("select path from tasks where channel='onchain_fills' and status in ('downloaded','shared')")]
    print("files:", len(files), flush=True)
    TMP.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("PRAGMA threads=6"); con.execute("PRAGMA memory_limit='20GB'"); con.execute(f"PRAGMA temp_directory='{TMP}'")
    con.execute("PRAGMA preserve_insertion_order=false")
    con.execute(f"""create table cat as
        select market_id, slug, asset_id_0, asset_id_1, result_id, status,
               cast(regexp_extract(slug, '(\\d+)$', 1) as bigint) as start_ts
        from read_parquet('{CATALOG}') where exchange='polymarket' and slug like 'btc-updown-5m-%'""")
    if PARTY.exists():
        shutil.rmtree(PARTY)
    PARTY.mkdir()
    base = f"""from read_parquet({files!r}) r join cat c using (market_id)"""
    common = """c.start_ts, r.tx_hash, r.log_index, r.block_timestamp_us as ts, (r.block_timestamp_us/1000000.0 - c.start_ts) as t_rel_s,
                r.builder <> '0x0000000000000000000000000000000000000000000000000000000000000000' as has_builder,
                cast(r.amount as double) as shares"""
    pm = "case when r.mirrored then 1-cast(r.price as double) else cast(r.price as double) end"
    con.execute(f"""copy (select {common}, r.maker as wallet, 'maker' as role, r.taker as counterparty,
            case when r.maker_asset_id = c.asset_id_0 then 0 else 1 end as outcome_idx, r.maker_side as side,
            {pm} as price, cast(0.0 as double) as fee {base}) to '{PARTY}/maker.parquet' (format parquet, compression zstd)""")
    print("maker rows written", flush=True)
    con.execute(f"""copy (select {common}, r.taker as wallet, 'taker' as role, r.maker as counterparty,
            case when r.taker_asset_id = c.asset_id_0 then 0 else 1 end as outcome_idx, r.taker_side as side,
            case when r.taker_asset_id = r.maker_asset_id then {pm} else 1 - ({pm}) end as price,
            cast(r.taker_fee as double) as fee {base}) to '{PARTY}/taker.parquet' (format parquet, compression zstd)""")
    print("taker rows written", flush=True)
    p = f"read_parquet('{PARTY}/*.parquet')"
    print(con.execute(f"select count(*) n, count(distinct wallet) wallets, count(distinct start_ts) mkts, min(t_rel_s) mn_t, max(t_rel_s) mx_t from {p}").fetchdf().to_string(), flush=True)
    con.execute(f"""create table wm as
        select wallet, start_ts,
               count(*) n_fills, sum((role='taker')::int) n_taker, sum((role='maker')::int) n_maker,
               sum(case when side='buy' then -shares*price else shares*price end - fee) cash, sum(fee) fee,
               sum(case when outcome_idx=0 then (case when side='buy' then shares else -shares end) else 0 end) net_up,
               sum(case when outcome_idx=1 then (case when side='buy' then shares else -shares end) else 0 end) net_down,
               sum(case when side='buy' then shares*price else 0 end) buy_notional,
               sum(case when side='sell' then shares*price else 0 end) sell_notional,
               sum(case when side='buy' then shares else 0 end) buy_shares,
               sum(case when side='sell' then shares else 0 end) sell_shares,
               sum(case when side='buy' and outcome_idx=0 then shares else 0 end) buy_up_shares,
               sum(case when side='buy' and outcome_idx=1 then shares else 0 end) buy_down_shares,
               min(t_rel_s) first_t, max(t_rel_s) last_t,
               sum(case when role='taker' then shares*price else 0 end) taker_notional,
               sum(case when role='maker' then shares*price else 0 end) maker_notional,
               sum(has_builder::int) n_builder
        from {p} group by 1,2""")
    con.execute("""create table wm2 as
        select w.*, c.market_id, c.result_id, c.status,
               case when c.result_id='0' then net_up when c.result_id='1' then net_down else null end as payout,
               cash + case when c.result_id='0' then net_up when c.result_id='1' then net_down else 0 end as pnl,
               c.result_id in ('0','1') as resolved,
               cast(to_timestamp(w.start_ts) as date) as market_date
        from wm w join cat c using (start_ts)""")
    inv = con.execute("""select count(*) n_mkts, max(abs(s_pnl + s_fee)) max_dev from (
        select start_ts, sum(pnl) s_pnl, sum(fee) s_fee from wm2 where resolved group by 1)""").fetchone()
    print("invariant per market: n=%d max|sum(pnl)+sum(fee)|=%.6f" % inv, flush=True)
    con.execute(f"copy wm2 to '{HERE}/WALLET_MARKET_LEDGER.parquet' (format parquet, compression zstd)")
    print(con.execute("select count(*) wm_rows, count(distinct wallet) wallets, count(distinct start_ts) mkts, sum(resolved::int) resolved_rows, round(sum(fee),2) fees, round(sum(pnl) filter (where resolved),2) pnl_sum from wm2").fetchdf().to_string(), flush=True)


if __name__ == "__main__":
    main()
