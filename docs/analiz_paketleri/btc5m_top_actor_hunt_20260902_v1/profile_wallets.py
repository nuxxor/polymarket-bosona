#!/usr/bin/env python3
"""Per-wallet fill-level profile from FILL_PARTY_LEDGER (no external clock needed)."""
import json, sys
from pathlib import Path
import duckdb, pandas as pd
HERE = Path(__file__).resolve().parent
P = f"read_parquet('{HERE}/FILL_PARTY_LEDGER/*.parquet')"
WM = f"read_parquet('{HERE}/WALLET_MARKET_LEDGER.parquet')"
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)

def profile(con, w):
    out = {}
    con.execute(f"""create or replace temp table f as
        select p.*, c.result_id, (p.outcome_idx::varchar = c.result_id) as asset_won, c.resolved
        from {P} p join (select start_ts, result_id, resolved from {WM} where wallet='{w}') c using (start_ts)
        where p.wallet='{w}' and c.resolved""")
    out["roles"] = con.execute("""select role, side, count(*) n, round(sum(shares*price)) notional, round(avg(shares),1) avg_sh, round(quantile_cont(shares,0.5),1) med_sh, round(quantile_cont(shares,0.9),1) p90_sh, round(sum(fee)) fee from f group by 1,2 order by 1,2""").fetchdf()
    out["timing"] = con.execute("""select case when t_rel_s < -60 then 'a<-60' when t_rel_s<0 then 'b-60..0' when t_rel_s<30 then 'c0..30' when t_rel_s<60 then 'd30..60' when t_rel_s<120 then 'e60..120' when t_rel_s<180 then 'f120..180' when t_rel_s<240 then 'g180..240' when t_rel_s<270 then 'h240..270' when t_rel_s<300 then 'i270..300' else 'j>=300' end tb,
        count(*) n, round(sum(shares*price)) notional, round(sum(case when side='buy' then shares*(asset_won::int - price) else shares*(price - asset_won::int) end)) gross_edge, round(sum(fee)) fee from f group by 1 order by 1""").fetchdf()
    out["price_buy"] = con.execute("""select role, floor(price*10)/10 pb, count(*) n, round(sum(shares)) sh, round(avg(price),3) avgp, round(sum(shares*asset_won::int)/sum(shares),3) winrate, round(sum(shares*(asset_won::int-price))) gross_edge, round(sum(fee)) fee from f where side='buy' group by 1,2 order by 1,2""").fetchdf()
    out["price_sell"] = con.execute("""select role, floor(price*10)/10 pb, count(*) n, round(sum(shares)) sh, round(avg(price),3) avgp, round(sum(shares*asset_won::int)/sum(shares),3) sold_asset_winrate, round(sum(shares*(price-asset_won::int))) gross_edge from f where side='sell' group by 1,2 order by 1,2""").fetchdf()
    out["hour"] = con.execute(f"""select hour(to_timestamp(start_ts)) h, count(*) n_mkts, round(sum(pnl)) pnl, round(sum(fee)) fee from {WM} where wallet='{w}' and resolved group by 1 order by 1""").fetchdf()
    out["market_dist"] = con.execute(f"""select count(*) n, round(quantile_cont(pnl,0.01)) p01, round(quantile_cont(pnl,0.05)) p05, round(quantile_cont(pnl,0.25)) p25, round(quantile_cont(pnl,0.5)) p50, round(quantile_cont(pnl,0.75)) p75, round(quantile_cont(pnl,0.95)) p95, round(quantile_cont(pnl,0.99)) p99, round(min(pnl)) mn, round(max(pnl)) mx,
        round(avg((buy_up_shares>0 and buy_down_shares>0)::int),3) two_sided, round(avg(buy_notional)) avg_buy_notional, round(avg(n_fills),1) avg_fills,
        round(sum(case when buy_up_shares>0 and buy_down_shares>0 then pnl else 0 end)) pnl_two_sided, round(sum(case when not (buy_up_shares>0 and buy_down_shares>0) then pnl else 0 end)) pnl_one_sided,
        round(avg(case when buy_up_shares>0 and buy_down_shares>0 then least(buy_up_shares,buy_down_shares)/greatest(buy_up_shares,buy_down_shares) end),3) pair_balance
        from {WM} where wallet='{w}' and resolved""").fetchdf()
    out["pair_cost"] = con.execute(f"""select round(quantile_cont(pc,0.1),3) p10, round(quantile_cont(pc,0.5),3) p50, round(quantile_cont(pc,0.9),3) p90, round(avg(pc),4) mean, count(*) n from (
        select start_ts, sum(case when outcome_idx=0 and side='buy' then shares*price end)/sum(case when outcome_idx=0 and side='buy' then shares end) + sum(case when outcome_idx=1 and side='buy' then shares*price end)/sum(case when outcome_idx=1 and side='buy' then shares end) pc
        from f group by 1) where pc is not null""").fetchdf()
    out["counterparties"] = con.execute(f"""select cp.counterparty, count(*) n, round(sum(cp.shares*cp.price)) notional, round(l.pnl) cp_total_pnl, round(l.fee) cp_fee, l.n_markets cp_mkts
        from f cp left join (select wallet, sum(pnl) pnl, sum(fee) fee, count(*) n_markets from {WM} where resolved group by 1) l on l.wallet=cp.counterparty
        group by 1, l.pnl, l.fee, l.n_markets order by notional desc limit 8""").fetchdf()
    out["builder"] = con.execute("select has_builder, count(*) n from f group by 1").fetchdf()
    out["first_last"] = con.execute("""select round(quantile_cont(ft,0.5)) med_first, round(quantile_cont(lt,0.5)) med_last, round(quantile_cont(span,0.5)) med_span, round(avg(nf),1) avg_fills from (select start_ts, min(t_rel_s) ft, max(t_rel_s) lt, max(t_rel_s)-min(t_rel_s) span, count(*) nf from f group by 1)""").fetchdf()
    return out

def main():
    wallets = sys.argv[1:]
    con = duckdb.connect(); con.execute("PRAGMA memory_limit='16GB'"); con.execute("PRAGMA threads=6")
    (HERE / "PROFILES").mkdir(exist_ok=True)
    for w in wallets:
        out = profile(con, w)
        lines = [f"# {w}\n"]
        for k, v in out.items():
            lines.append(f"## {k}\n\n```\n{v.to_string(index=False)}\n```\n")
        (HERE / "PROFILES" / f"{w}.md").write_text("\n".join(lines))
        print(f"\n{'='*100}\n{w}")
        for k in ("roles", "timing", "price_buy", "price_sell", "market_dist", "pair_cost", "counterparties", "first_last"):
            print(f"-- {k}"); print(out[k].to_string(index=False))

if __name__ == "__main__":
    main()
