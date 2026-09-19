#!/usr/bin/env python3
"""State-at-fill features vs Binance spot (100ms) for target wallets + controls, with a TWAP60-aware fair value.

Settlement: S = mean(P) over [240,300]s vs reference P_ref (TWAP of [-60,0)s, 'twap' ref; also spot-at-0 for comparison).
At time t: known part of S = mean over [240, t) (if t>240); unknown part expectation = P_t; sd = sigma*P_t*sqrt(tau0 + L/3)*(L/60),
tau0 = max(240-t,0), L = 300 - clamp(t,240,300). fair_up = Phi((E_S - P_ref)/sd).
"""
import sqlite3, sys
from pathlib import Path
import duckdb, pandas as pd
HERE = Path(__file__).resolve().parent
TARGETS = [l.strip() for l in (HERE / "TARGET_WALLETS.txt").read_text().split() if l.strip()]
con = duckdb.connect(); con.execute("PRAGMA memory_limit='20GB'"); con.execute("PRAGMA threads=6")
con.execute(f"PRAGMA temp_directory='/tmp/claude-1000/-home-taygun-Masa-st--polymarket/361c82d8-4092-4426-9c1b-657e6613e879/scratchpad/duck_tmp'")
con.execute("""create macro erf(x) as (case when x >= 0 then 1 else -1 end) * (1 - (((((1.061405429*(1/(1+0.3275911*abs(x))) - 1.453152027)*(1/(1+0.3275911*abs(x))) + 1.421413741)*(1/(1+0.3275911*abs(x))) - 0.284496736)*(1/(1+0.3275911*abs(x))) + 0.254829592)*(1/(1+0.3275911*abs(x)))*exp(-x*x)))""")
con.register("targets", pd.DataFrame({"wallet": TARGETS}))
con.execute(f"create table b as select bin_ms, last_px from read_parquet('{HERE}/BINANCE_SPOT_100MS.parquet') order by bin_ms")
con.execute(f"""create table mk as select start_ts, result_id from read_parquet('{HERE}/WALLET_MARKET_LEDGER.parquet') where resolved group by 1,2""")
# per-market references: twap ref over [-60,0), spot at 0, sigma from 1s returns over prior 30 min
con.execute("""create table b1 as select bin_ms//1000 as s, arg_max(last_px, bin_ms) px from b group by 1""")
con.execute("""create table ref as
  select m.start_ts,
    (select avg(last_px) from b where b.bin_ms >= (m.start_ts-60)*1000 and b.bin_ms < m.start_ts*1000) as p_ref_twap,
    (select arg_max(last_px, bin_ms) from b where b.bin_ms < m.start_ts*1000 and b.bin_ms >= (m.start_ts-10)*1000) as p_ref_spot,
    (select stddev_samp(r) from (select ln(px/lag(px) over (order by s)) r from b1 where b1.s >= m.start_ts-1800 and b1.s < m.start_ts)) as sigma_1s,
    (select avg(last_px) from b where b.bin_ms >= (m.start_ts+240)*1000 and b.bin_ms < (m.start_ts+300)*1000) as s_binance
  from mk m""")
print(con.execute("select count(*) n, sum((p_ref_twap is null)::int) null_ref, sum((sigma_1s is null)::int) null_sig, avg(sigma_1s)*1e4 sig_bps from ref").fetchdf().to_string(index=False), flush=True)
# settlement check: Binance-implied outcome vs official
print(con.execute("""select 'twap' ref, avg(((s_binance >= p_ref_twap)::int)::varchar = replace(result_id,'1','x')) dummy from ref join mk using(start_ts) limit 0""").fetchdf() if False else "")
print(con.execute("""select avg((case when s_binance >= p_ref_twap then '0' else '1' end = result_id)::int) agree_twap,
                            avg((case when s_binance >= p_ref_spot then '0' else '1' end = result_id)::int) agree_spot, count(*) n
                     from ref join mk using(start_ts) where s_binance is not null""").fetchdf().to_string(index=False), flush=True)
# known-part cumulative table for the settlement window at 100ms
con.execute("""create table kw as
  select m.start_ts, b.bin_ms, sum(b.last_px) over (partition by m.start_ts order by b.bin_ms) as cum_px, row_number() over (partition by m.start_ts order by b.bin_ms) as cum_n
  from mk m join b on b.bin_ms >= (m.start_ts+240)*1000 and b.bin_ms < (m.start_ts+300)*1000""")
# fills: targets (all rows) + control (2% of other taker rows) + top losers list
con.execute(f"""create table f0 as
  select p.start_ts, p.tx_hash, p.log_index, p.ts, p.wallet, p.role, p.side, p.outcome_idx, p.price, p.shares, p.fee, p.has_builder,
         case when p.wallet in (select wallet from targets) then 'target' else 'control' end grp
  from read_parquet('{HERE}/FILL_PARTY_LEDGER/*.parquet') p
  where p.wallet in (select wallet from targets) or (p.role='taker' and hash(p.tx_hash || p.wallet) % 50 = 0)""")
con.execute(f"""create table f1 as
  select f.*, coalesce(c.clob_ts/1000, f.ts/1000 - 2440) as fill_ms, (c.clob_ts is not null) as clock_clob,
         m.result_id, (f.outcome_idx::varchar = m.result_id) as won
  from f0 f join mk m using (start_ts) left join read_parquet('{HERE}/CLOB_TIMES.parquet') c using (start_ts, tx_hash)""")
print("fills:", con.execute("select grp, count(*) from f1 group by 1").fetchall(), flush=True)
def asof(col, shift_ms, src="f_cur", dst="f_next"):
    con.execute(f"""create table {dst} as select f.*, b.last_px as {col} from {src} f asof join b on f.fill_ms - {shift_ms} >= b.bin_ms""")
    con.execute(f"drop table {src}"); con.execute(f"alter table {dst} rename to {src}")
con.execute("create table f_cur as select * from f1"); con.execute("drop table f1")
asof("p_t", 0); asof("p_t5", 5000); asof("p_t15", 15000); asof("p_t30", 30000); asof("p_t60", 60000)
con.execute("""create table f2 as
  select f.*, r.p_ref_twap, r.p_ref_spot, r.sigma_1s, r.s_binance, k.cum_px, k.cum_n
  from f_cur f join ref r using (start_ts)
  asof left join kw k on f.start_ts = k.start_ts and f.fill_ms >= k.bin_ms""")
con.execute("""create table feat as
  select *, fill_ms/1000.0 - start_ts as t,
    1e4*ln(p_t/p_ref_twap) d_bps, 1e4*ln(p_t/p_ref_spot) d_spot_bps,
    1e4*ln(p_t/p_t5) mom5, 1e4*ln(p_t/p_t15) mom15, 1e4*ln(p_t/p_t30) mom30, 1e4*ln(p_t/p_t60) mom60,
    sigma_1s*1e4 sigma_bps
  from f2""")
con.execute("""create table feat2 as
  select *,
    greatest(240 - t, 0) as tau0,
    300 - least(greatest(t, 240), 300) as L,
    case when t > 240 and cum_n is not null then cum_n*0.1 else 0 end as known_len,
    case when t > 240 and cum_n is not null then cum_px/cum_n else null end as known_mean
  from feat""")
con.execute("""create table feat3 as
  select *,
    (coalesce(known_mean*known_len,0) + p_t*L)/greatest(known_len + L, 0.1) as e_s,
    sigma_1s*p_t*sqrt(tau0 + L/3.0)*(L/60.0) as sd_s,
    sigma_1s*p_t*sqrt(greatest(300-t,0.1)) as sd_naive
  from feat2""")
con.execute("""create table feat4 as
  select *,
    case when sd_s > 0 then 0.5*(1+erf(((e_s - p_ref_twap)/sd_s)/sqrt(2))) else (e_s >= p_ref_twap)::double end as fair_up,
    case when sd_naive > 0 then 0.5*(1+erf(((p_t - p_ref_twap)/sd_naive)/sqrt(2))) else (p_t >= p_ref_twap)::double end as fair_up_naive,
    case when sd_naive > 0 then 0.5*(1+erf(((p_t - p_ref_spot)/sd_naive)/sqrt(2))) else (p_t >= p_ref_spot)::double end as fair_up_spot
  from feat3""")
con.execute("""create table feat5 as
  select *, case when outcome_idx=0 then fair_up else 1-fair_up end as fair_asset,
             case when outcome_idx=0 then fair_up_naive else 1-fair_up_naive end as fair_asset_naive,
             case when side='buy' then (case when outcome_idx=0 then fair_up else 1-fair_up end) - price else price - (case when outcome_idx=0 then fair_up else 1-fair_up end) end as edge_model,
             case when side='buy' then won::int - price else price - won::int end as edge_real
  from feat4""")
con.execute(f"copy feat5 to '{HERE}/STATE_FEATURES.parquet' (format parquet, compression zstd)")
print(con.execute("select grp, role, count(*) n, avg(clock_clob::int) clob, round(avg(edge_model),4) edge_model, round(avg(edge_real),4) edge_real from feat5 group by 1,2 order by 1,2").fetchdf().to_string(index=False), flush=True)
# model calibration on a market grid
con.execute("""create table grid as select m.start_ts, m.result_id, g.t from mk m, (select unnest([0,30,60,90,120,150,180,210,240,255,270,285,295]) t) g""")
con.execute("create table g1 as select g.*, (g.start_ts + g.t)*1000 as fill_ms from grid g")
con.execute("create table g2 as select g.*, b.last_px p_t from g1 g asof join b on g.fill_ms >= b.bin_ms")
con.execute("""create table g3 as select g.*, r.p_ref_twap, r.p_ref_spot, r.sigma_1s, k.cum_px, k.cum_n from g2 g join ref r using (start_ts) asof left join kw k on g.start_ts = k.start_ts and g.fill_ms >= k.bin_ms""")
con.execute("""create table g4 as select *, greatest(240 - t, 0) tau0, 300 - least(greatest(t,240),300) L,
   case when t > 240 and cum_n is not null then cum_n*0.1 else 0 end known_len, case when t > 240 and cum_n is not null then cum_px/cum_n end known_mean from g3""")
con.execute("""create table g5 as select *, (coalesce(known_mean*known_len,0) + p_t*L)/greatest(known_len+L,0.1) e_s, sigma_1s*p_t*sqrt(tau0 + L/3.0)*(L/60.0) sd_s, sigma_1s*p_t*sqrt(greatest(300-t,0.1)) sd_naive from g4""")
con.execute("""create table g6 as select *,
   case when sd_s > 0 then 0.5*(1+erf(((e_s - p_ref_twap)/sd_s)/sqrt(2))) else (e_s >= p_ref_twap)::double end fair_up,
   case when sd_naive > 0 then 0.5*(1+erf(((p_t - p_ref_twap)/sd_naive)/sqrt(2))) else (p_t >= p_ref_twap)::double end fair_naive,
   case when sd_naive > 0 then 0.5*(1+erf(((p_t - p_ref_spot)/sd_naive)/sqrt(2))) else (p_t >= p_ref_spot)::double end fair_spot,
   (result_id='0')::int up from g5""")
con.execute(f"copy g6 to '{HERE}/MODEL_GRID.parquet' (format parquet, compression zstd)")
print(con.execute("""select t, count(*) n, round(avg(power(fair_up-up,2)),4) brier_twap, round(avg(power(fair_naive-up,2)),4) brier_naive, round(avg(power(fair_spot-up,2)),4) brier_spot,
   round(avg(((fair_up>=0.5)::int = up)::int),3) acc_twap, round(avg(((fair_spot>=0.5)::int = up)::int),3) acc_spot from g6 group by 1 order by 1""").fetchdf().to_string(index=False), flush=True)
print(con.execute("""select round(fair_up,1) fb, count(*) n, round(avg(up),3) realized from g6 where t in (60,120,180,240) group by 1 order by 1""").fetchdf().to_string(index=False), flush=True)
