#!/usr/bin/env python3
import sys
from pathlib import Path
import duckdb, pandas as pd
HERE = Path(__file__).resolve().parent
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
con = duckdb.connect(); con.execute("PRAGMA memory_limit='16GB'"); con.execute("PRAGMA threads=6")
con.execute(f"create view sf as select *, case when t<0 then 'a<0' when t<30 then 'b0-30' when t<60 then 'c30-60' when t<120 then 'd60-120' when t<180 then 'e120-180' when t<240 then 'f180-240' when t<270 then 'g240-270' when t<300 then 'h270-300' else 'i>=300' end tb, (side='buy' and ((outcome_idx=0 and d_bps>0) or (outcome_idx=1 and d_bps<0))) as with_d, (side='buy' and ((outcome_idx=0 and mom15>0) or (outcome_idx=1 and mom15<0))) as with_mom15 from read_parquet('{HERE}/STATE_FEATURES.parquet')")
def tbl(w, role, side):
    return con.execute(f"""select tb, count(*) n, round(sum(shares*price)) notional, round(avg(price),3) price, round(avg(fair_asset),3) fair, round(avg(edge_model),4) edge_model, round(avg(edge_real),4) edge_real,
        round(avg((fair_asset > price)::int),3) below_fair, round(avg(with_d::int),3) with_d, round(avg(with_mom15::int),3) with_mom15, round(avg(abs(d_bps)),1) abs_d, round(avg(abs(mom5)),2) abs_mom5, round(avg(sigma_bps),3) sig
        from sf where wallet='{w}' and role='{role}' and side='{side}' group by 1 order by 1""").fetchdf()
def calib(w, role='taker', side='buy'):
    return con.execute(f"""select round(fair_asset*10)/10 fb, count(*) n, round(avg(price),3) price, round(avg(fair_asset),3) fair, round(avg(won::int),3) realized, round(avg(won::int)-avg(fair_asset),3) beyond_model
        from sf where wallet='{w}' and role='{role}' and side='{side}' group by 1 order by 1""").fetchdf()
for w in sys.argv[1:]:
    print(f"\n{'#'*110}\n{w}")
    for role, side in (("taker","buy"),("maker","buy"),("taker","sell"),("maker","sell")):
        d = tbl(w, role, side)
        if len(d): print(f"-- {role} {side}"); print(d.to_string(index=False))
    for role in ("taker","maker"):
        c = calib(w, role)
        if len(c): print(f"-- calibration {role} buy (realized vs model)"); print(c.to_string(index=False))
print("\n-- CONTROL taker buy"); print(con.execute("""select tb, count(*) n, round(avg(price),3) price, round(avg(fair_asset),3) fair, round(avg(edge_model),4) edge_model, round(avg(edge_real),4) edge_real, round(avg((fair_asset > price)::int),3) below_fair, round(avg(with_d::int),3) with_d, round(avg(with_mom15::int),3) with_mom15 from sf where grp='control' and side='buy' group by 1 order by 1""").fetchdf().to_string(index=False))
print("-- CONTROL calibration"); print(con.execute("""select round(fair_asset*10)/10 fb, count(*) n, round(avg(price),3) price, round(avg(fair_asset),3) fair, round(avg(won::int),3) realized from sf where grp='control' and side='buy' group by 1 order by 1""").fetchdf().to_string(index=False))
