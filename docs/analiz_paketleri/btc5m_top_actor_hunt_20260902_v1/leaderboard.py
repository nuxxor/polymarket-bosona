#!/usr/bin/env python3
"""Wallet leaderboard + regularity metrics from WALLET_MARKET_LEDGER.parquet."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
rng = np.random.default_rng(20260902)


def day_bootstrap_lb(daily: np.ndarray, n=4000) -> float:
    if len(daily) < 3:
        return float("nan")
    idx = rng.integers(0, len(daily), size=(n, len(daily)))
    return float(np.quantile(daily[idx].sum(axis=1), 0.025))


def signflip_p(daily: np.ndarray, n=4000) -> float:
    if len(daily) < 3:
        return float("nan")
    s = daily.sum()
    flips = rng.choice([-1, 1], size=(n, len(daily))) * daily
    return float((np.abs(flips.sum(axis=1)) >= abs(s)).mean())


def main() -> None:
    wm = pd.read_parquet(HERE / "WALLET_MARKET_LEDGER.parquet")
    wm = wm[wm.resolved].copy()
    wm["market_date"] = pd.to_datetime(wm.market_date)
    wm["two_sided"] = (wm.buy_up_shares > 0) & (wm.buy_down_shares > 0)
    g = wm.groupby("wallet")
    lb = pd.DataFrame({
        "pnl": g.pnl.sum(), "fee": g.fee.sum(), "n_markets": g.size(),
        "n_fills": g.n_fills.sum(), "taker_fill_share": g.n_taker.sum() / g.n_fills.sum(),
        "taker_notional_share": g.taker_notional.sum() / (g.taker_notional.sum() + g.maker_notional.sum()),
        "buy_notional": g.buy_notional.sum(), "sell_notional": g.sell_notional.sum(),
        "sell_share": g.sell_shares.sum() / g.buy_shares.sum().replace(0, np.nan),
        "two_sided_share": g.two_sided.mean(),
        "win_markets": g.pnl.apply(lambda s: (s > 0).mean()),
        "first_day": g.market_date.min().dt.date, "last_day": g.market_date.max().dt.date,
        "median_first_t": g.first_t.median(),
    })
    lb["roi"] = lb.pnl / lb.buy_notional.replace(0, np.nan)
    pos = g.pnl.apply(lambda s: s[s > 0].sum()); neg = g.pnl.apply(lambda s: -s[s < 0].sum())
    lb["profit_factor"] = pos / neg.replace(0, np.nan)
    top3 = g.pnl.apply(lambda s: s.nlargest(3).sum()); lb["pnl_ex_top3"] = lb.pnl - top3
    lb["best_mkt_share"] = g.pnl.max() / lb.pnl.replace(0, np.nan)
    daily = wm.groupby(["wallet", "market_date"]).pnl.sum().reset_index()
    dg = daily.groupby("wallet").pnl
    lb["n_days"] = dg.size(); lb["pos_days"] = dg.apply(lambda s: (s > 0).sum())
    lb["pos_day_share"] = lb.pos_days / lb.n_days
    lb["daily_mean"] = dg.mean(); lb["daily_std"] = dg.std()
    lb["daily_t"] = lb.daily_mean / (lb.daily_std / np.sqrt(lb.n_days))
    lb["worst_day"] = dg.min(); lb["best_day"] = dg.max()
    # drawdown on daily cumulative
    def mdd(s):
        c = s.cumsum(); return float((c.cummax() - c).max())
    lb["max_dd"] = dg.apply(mdd)
    cand = lb[lb.pnl > 500].index
    lb["boot_lb95"] = np.nan; lb["signflip_p"] = np.nan
    for w in cand:
        d = daily[daily.wallet == w].pnl.to_numpy()
        lb.loc[w, "boot_lb95"] = day_bootstrap_lb(d); lb.loc[w, "signflip_p"] = signflip_p(d)
    lb = lb.sort_values("pnl", ascending=False)
    lb.to_csv(HERE / "LEADERBOARD_ALL.csv")
    daily.to_parquet(HERE / "WALLET_DAILY.parquet")
    reg = lb[(lb.n_days >= 12) & (lb.pos_day_share >= 0.6) & (lb.pnl_ex_top3 > 0) & (lb.daily_t >= 2)]
    reg.to_csv(HERE / "LEADERBOARD_REGULAR.csv")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    cols = ["pnl", "fee", "n_markets", "n_days", "pos_day_share", "daily_t", "boot_lb95", "pnl_ex_top3", "profit_factor", "roi", "taker_fill_share", "sell_share", "two_sided_share", "win_markets", "median_first_t", "max_dd"]
    print("=== TOP 25 by PnL (all) ==="); print(lb[cols].head(25).round(3).to_string())
    print("\n=== REGULAR WINNERS (n_days>=12, pos_day_share>=0.6, pnl_ex_top3>0, daily_t>=2) ==="); print(reg[cols].head(25).round(3).to_string())
    print("\n=== BOTTOM 10 ==="); print(lb[cols].tail(10).round(3).to_string())
    print("\nwallets:", len(lb), "sum pnl:", round(lb.pnl.sum(), 2), "sum fee:", round(lb.fee.sum(), 2))


if __name__ == "__main__":
    main()
