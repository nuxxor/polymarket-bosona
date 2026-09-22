"""Independent read-only checks of frozen context fields and fixed five-share probes."""

from collections import defaultdict
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
REVIEW = OUT.parent
DATA = OUT.parents[1]


def read(path):
    return json.loads(path.read_text())


def five_cash(book, rate, buy):
    if not book:
        return None
    ladder = book.get("asks" if buy else "bids")
    if ladder is None:
        if buy and book.get("ask5_cash") is not None:
            return D(str(book["ask5_cash"]))
        price = book["ask" if buy else "bid"]
        depth = book["ask_top_q" if buy else "bid_top_q"]
        if price is None or depth is None or depth < 5:
            return None
        ladder = [(price, depth)]
    quantity, gross, fees = D(5), D(0), D(0)
    for pp, qq in sorted(ladder, reverse=not buy):
        p, available = D(str(pp)), D(str(qq))
        assert 0 < p <= 1 and available >= 0
        take = min(quantity, available)
        gross += p * take
        fees += take * rate * p * (1 - p)
        quantity -= take
        if quantity <= D(".00000001"):
            return gross + fees.quantize(D(".00001")) * (1 if buy else -1)
    return None


def main():
    paths = [
        REVIEW / "context/events.json",
        REVIEW / "context/reconstruct.py",
        REVIEW / "mechanisms.py",
    ]
    inputs = {
        str(p.relative_to(REVIEW)): sha256(p.read_bytes()).hexdigest() for p in paths
    }
    events = read(paths[0])
    fills = read(DATA / "btc5m_parent_research_20260921/report.json")["fills"]
    by_start = defaultdict(list)
    for f in fills:
        by_start[f["S"]].append(f)
    probe_rows, same_net_activity, ws_after_claim = [], [], []
    checks, cached_fallback = 0, 0
    rounding_differences = []
    for r in events:
        nominal = [f for f in by_start[r["S"]] if f["ts"] < r["ts"]]
        nominal_net = sum(f["qty"] * (1 if f["outcome"] == 0 else -1) for f in nominal)
        assert nominal_net == r["net_before_units"]
        for lag in ("lag5", "lag10"):
            c = r[lag]
            now = c["now_ms"]
            prior = [f for f in by_start[r["S"]] if f["ts"] * 1000 <= now]
            net = sum(f["qty"] * (1 if f["outcome"] == 0 else -1) for f in prior)
            assert net == c["net_at_cutoff_units"]
            held = 0 if net > 0 else 1 if net < 0 else None
            assert held == c["held_side"]
            assert (net != nominal_net) == c["inventory_changed_since_cut"]
            between = [f for f in nominal if f["ts"] * 1000 > now]
            if between and net == nominal_net:
                same_net_activity.append(
                    dict(
                        S=r["S"],
                        ts=r["ts"],
                        lag=lag,
                        kind=r["kind"],
                        fills=len(between),
                    )
                )
            for field in ("reference", "spot", "twap60"):
                v = c.get(field)
                if v:
                    assert v["received_ms"] <= now and v["observed_ms"] <= now
            if c["before_all_matched_ws_observations"] is False:
                ws_after_claim.append(dict(S=r["S"], ts=r["ts"], lag=lag))
            rate = D(str(c["archived_fee_rate_assumption"]))
            for quantity in ("5", "inventory", "actor_reducing"):
                buy = c.get("opposite_buy_" + quantity)
                sell = c.get("held_sell_" + quantity)
                if buy and sell:
                    independent = (
                        D(str(buy["quantity"]))
                        - D(str(buy["cash"]))
                        - D(str(sell["cash"]))
                    )
                    assert abs(
                        independent - D(str(c["opposite_buy_advantage_" + quantity]))
                    ) < D("1e-8")
            if r["kind"] != "control":
                continue
            x = c["execution250"]
            assert x["target_ms"] == now + 250 and x["execution_only_not_signal"]
            snapshot = x["book"]
            if snapshot:
                assert snapshot["snapshot_ms"] == now + 250
                for b in snapshot["books"]:
                    if b:
                        assert 0 <= now + 250 - b["observed_ms"] <= 3000
                        assert 0 <= now + 250 - b["received_ms"] <= 3000
            for label, side, buy in [
                ("opposite_buy_5", 1 - held if held is not None else None, True),
                ("held_sell_5", held, False),
            ]:
                b = snapshot["books"][side] if snapshot and side is not None else None
                expected = five_cash(b, rate, buy)
                actual = x[label]
                assert (expected is None) == (actual is None)
                if expected is not None:
                    difference = expected - D(str(actual["cash"]))
                    assert abs(difference) < D(".000010011"), (expected, actual)
                    if abs(difference) > D(".000000011"):
                        rounding_differences.append(
                            dict(
                                S=r["S"],
                                lag=lag,
                                age=r["age"],
                                leg=label,
                                decimal_cash=str(expected),
                                float_cash=actual["cash"],
                                difference=str(difference),
                                rate=str(rate),
                            )
                        )
                    checks += 1
                    cached_fallback += bool(b and "asks" not in b and buy)
            quote = x["opposite_buy_5"]
            if abs(net) < 5_000_000 or quote is None:
                continue
            cost = D(str(quote["cash"]))
            winner = r["outcome_label"]["winner"]
            gross_up = sum(f["qty"] for f in prior if f["outcome"] == 0) / 1_000_000
            gross_down = sum(f["qty"] for f in prior if f["outcome"] == 1) / 1_000_000
            before = [D(str(gross_up)), D(str(gross_down))]
            after = before.copy()
            after[1 - held] += 5
            # Independent terminal-wealth subtraction, old cash drops out.
            delta = after[winner] - cost - before[winner]
            assert delta == D(5) - cost - (D(5) if held == winner else D(0))
            assert abs(net) - 5_000_000 >= 0
            probe_rows.append(
                dict(
                    S=r["S"],
                    lag=lag,
                    age=r["age"],
                    cash=float(cost),
                    delta=float(delta),
                )
            )
    summaries = defaultdict(lambda: dict(n=0, delta=0.0))
    for r in probe_rows:
        group = summaries[r["lag"] + "_nominal" + str(r["age"])]
        group["n"] += 1
        group["delta"] += r["delta"]
    old = read(REVIEW / "mechanisms.json")
    source_current = (
        old["source_sha256"]["context/events.json"] == inputs["context/events.json"]
    )
    for k, v in summaries.items():
        if source_current:
            compare = old["fixed_probe_economics"][k]["all_close"]
            assert v["n"] == compare["n"] and abs(v["delta"] - compare["delta"]) < 1e-8
    result = dict(
        status="PASS",
        source_sha256=inputs,
        context_events=len(events),
        controls=sum(r["kind"] == "control" for r in events),
        execution_quotes_checked=checks,
        quote_checks_using_cached_cash_not_raw_ladder=cached_fallback,
        usable_probe_rows=len(probe_rows),
        economics=dict(summaries),
        existing_mechanisms_matches_current_context=source_current,
        fee_rounding_differences=rounding_differences,
        rounding_check="Decimal ROUND_HALF_EVEN sensitivity versus inherited float round; official tie rule not asserted.",
        activity_between_cutoff_and_event_with_unchanged_net=same_net_activity,
        causal_cut_after_matched_public_ws=ws_after_claim,
        limitations=[
            "Net stability is not full inventory or no-fill stability.",
            "Position age fields measure first/last historical fill, not age since last flat/reversal.",
            "Public-second inventory cannot prove exact local knowledge at the cutoff.",
            "Cached five-share cash independently rechecked only against cache, not raw ladders.",
            "Replayed displayed depth and250ms snapshot remain conditional execution estimates, not filled orders.",
        ],
    )
    (OUT / "crosscheck.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "fee_rounding_differences"},
            indent=2,
        )
    )
    print("Rounding sensitivity count:", len(rounding_differences))


if __name__ == "__main__":
    assert five_cash({"asks": [[0.4, 4]]}, D(".07"), True) is None
    assert five_cash({"asks": [[0.4, 5]]}, D(".07"), True) == D("2.08400")
    main()
