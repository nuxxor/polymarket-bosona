#!/usr/bin/env python3
"""Binance spot signed flow (taker buy - taker sell volume, 100ms bins) and its relation to 0xce50's entries + generic predictive power."""
import glob
from pathlib import Path
import duckdb, pandas as pd
pd.set_option("display.width", 250)
HERE = Path(__file__).resolve().parent
TMP = Path("/tmp/claude-1000/-home-taygun-Masa-st--polymarket/361c82d8-4092-4426-9c1b-657e6613e879/scratchpad/binance_csv")
csvs = sorted(glob.glob(str(TMP / "2026-*.csv")))
con = duckdb.connect(); con.execute("PRAGMA threads=6"); con.execute("PRAGMA memory_limit='20GB'")
con.execute(f"""create table flow as
  select bin_ms, sum(case when is_bm then -q else q end) signed_q, sum(q) q, sum(case when is_bm then -q*px else q*px end) signed_usd
  from (select column1::double px, column2::double q, column6::boolean is_bm,
        ((case when column5::bigint > 1000000000000000 then column5::bigint // 1000 else column5::bigint end) // 100)*100 as bin_ms
        from read_csv({csvs!r}, header=false, columns={{'column0':'BIGINT','column1':'DOUBLE','column2':'DOUBLE','column3':'BIGINT','column4':'BIGINT','column5':'BIGINT','column6':'BOOLEAN','column7':'BOOLEAN'}}))
  group by 1""")
con.execute("create table flow1s as select bin_ms//1000 s, sum(signed_usd) su, sum(abs(signed_usd)) au from flow group by 1")
con.execute("create table fs as select s, su, au, sum(su) over (order by s) cum_su, sum(au) over (order by s) cum_au from flow1s")
con.execute(f"copy fs to '{HERE}/BINANCE_FLOW_1S.parquet' (format parquet, compression zstd)")
# fills of interest
ws = ['0xce50c96b976203b53342a0a801067d2cdcfcf46e','0x32ed2e546b187ca15e2841edc82b22c713cf8ec3','0x20d2309cd92b797ae7ca175ed828ed8a27fbe29d']
con.register('ws', pd.DataFrame({'wallet': ws}))
con.execute(f"""create table f as select wallet, grp, role, outcome_idx, price, fair_asset, won, t, fill_ms, p_t, s_binance, sigma_bps, case when outcome_idx=0 then 1 else -1 end sgn, fill_ms//1000 as s
   from read_parquet('{HERE}/STATE_FEATURES.parquet') where side='buy' and t>=0 and t<300 and role='taker' and (wallet in (select wallet from ws) or grp='control')""")
for h in (10, 30, 60, 120, 300):
    con.execute(f"""create table f2 as select f.*, (a.cum_su - b.cum_su) as imb{h}, (a.cum_au - b.cum_au) as act{h}
        from f asof join fs a on f.s >= a.s asof join fs b on f.s - {h} >= b.s""")
    con.execute("drop table f"); con.execute("alter table f2 rename to f")
print(con.execute("""select case when grp='control' then 'CONTROL' else substr(wallet,1,10) end w, count(*) n,
   round(avg((sgn*imb10>0)::int),3) agree10, round(avg((sgn*imb30>0)::int),3) agree30, round(avg((sgn*imb60>0)::int),3) agree60, round(avg((sgn*imb120>0)::int),3) agree120, round(avg((sgn*imb300>0)::int),3) agree300,
   round(avg(sgn*imb60)/1000) mean_signed_imb60_k, round(avg(act60)/1000) act60_k
   from f group by 1 order by 1""").fetchdf().to_string(index=False))
print(con.execute("""select substr(wallet,1,10) w, case when t<60 then 'a0-60' when t<120 then 'b60-120' when t<180 then 'c120-180' when t<240 then 'd180-240' else 'e240-300' end tb, count(*) n,
   round(avg((sgn*imb30>0)::int),3) agree30, round(avg((sgn*imb60>0)::int),3) agree60, round(avg((sgn*imb120>0)::int),3) agree120, round(avg(won::int),3) won
   from f where wallet='0xce50c96b976203b53342a0a801067d2cdcfcf46e' group by 1,2 order by 1,2""").fetchdf().to_string(index=False))
# generic predictive power of imbalance for next-60s return on a market grid (t=60,120,180) split by sigma regime and hour
con.execute(f"""create table g as select start_ts, t, p_t, sigma_1s*1e4 sigma_bps, (start_ts+t) s, (start_ts+t)*1000 fill_ms, hour(to_timestamp(start_ts)) h from read_parquet('{HERE}/MODEL_GRID.parquet') where t in (60,120,180)""")
con.execute(f"create table b as select bin_ms, last_px from read_parquet('{HERE}/BINANCE_SPOT_100MS.parquet')")
con.execute("create table g2 as select g.*, b.last_px p60 from g asof join b on g.fill_ms + 60000 >= b.bin_ms")
con.execute("create table g3 as select g.*, (a.cum_su-c.cum_su) imb60, (a.cum_su-d.cum_su) imb120 from g2 g asof join fs a on g.s >= a.s asof join fs c on g.s-60 >= c.s asof join fs d on g.s-120 >= d.s")
print(con.execute("""select case when sigma_bps<0.45 then 'calm' else 'active' end regime, case when h between 4 and 11 then 'h04-11' else 'other' end hb, ntile(5) over (partition by (sigma_bps<0.45), (h between 4 and 11) order by imb60) q, count(*) n, round(avg(imb60)/1000) imb60_k, round(avg(1e4*ln(p60/p_t)),2) fut60_bps
   from g3 group by 1,2, q order by 1,2,3""").fetchdf() if False else con.execute("""with x as (select *, ntile(5) over (partition by (sigma_bps<0.45), (h between 4 and 11) order by imb60) q from g3)
   select case when sigma_bps<0.45 then 'calm' else 'active' end regime, case when h between 4 and 11 then 'h04-11' else 'other' end hb, q, count(*) n, round(avg(imb60)/1000) imb60_k, round(avg(1e4*ln(p60/p_t)),2) fut60_bps from x group by 1,2,3 order by 1,2,3""").fetchdf().to_string(index=False))
