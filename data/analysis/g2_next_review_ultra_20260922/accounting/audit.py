"""Offline accounting/parent audit. Writes only beside this script; no network."""

from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import importlib.util
from itertools import permutations
import json
from pathlib import Path
import random
from statistics import median
import sys

sys.dont_write_bytecode = True

OUT = Path(__file__).resolve().parent
DATA = OUT.parents[1]
R1 = DATA / "btc5m_parent_research_20260921"
UNIT = 1_000_000
INPUTS = {}


def read(path):
    raw = path.read_bytes()
    INPUTS[str(path.relative_to(DATA))] = sha256(raw).hexdigest()
    return json.loads(raw)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    INPUTS[str(path.relative_to(DATA))] = sha256(path.read_bytes()).hexdigest()
    return obj


def units(value):
    value = Decimal(str(value)) * UNIT
    assert value == int(value)
    return int(value)


def day(start):
    return datetime.fromtimestamp(start, timezone.utc).strftime("%Y-%m-%d")


def key(row):
    return tuple(
        str(row.get(k, ""))
        for k in (
            "transactionHash",
            "timestamp",
            "type",
            "asset",
            "outcomeIndex",
            "side",
            "size",
            "price",
            "usdcSize",
        )
    )


def action(net, signed):
    return (
        "open"
        if not net
        else "add"
        if net * signed > 0
        else "reduce"
        if abs(signed) <= abs(net)
        else "reverse"
    )


def first_reduction(fs, winner):
    seconds = defaultdict(list)
    for f in fs:
        seconds[f["ts"]].append(f)
    net, lots = 0, []
    for ts, group in sorted(seconds.items()):
        sides = {f["outcome"] for f in group}
        if len(sides) > 1:
            return {"status": "ambiguous_first_reduction_both_sides", "ts": ts}
        (side,) = sides
        sign = 1 if side == 0 else -1
        if net * sign < 0:
            parents = {f["order_hash"] for f in group}
            if ts >= group[0]["S"] + 300:
                return {
                    "status": "ambiguous_first_reduction_after_public_end",
                    "ts": ts,
                }
            if len(parents) != 1:
                return {
                    "status": "ambiguous_first_reduction_multiple_parents",
                    "ts": ts,
                }
            qty = sum(f["qty"] for f in group)
            close = min(qty, abs(net))
            prices = [Fraction(f["cash_cost"], f["qty"]) for f in group]
            if qty > close and float(max(prices) - min(prices)) > 1e-8:
                return {"status": "ambiguous_overshoot_allocation", "ts": ts}
            price = Fraction(sum(f["cash_cost"] for f in group), qty)
            remain, cost = close, Fraction(0)
            for amount, old_price in sorted(lots, key=lambda x: x[1]):
                use = min(amount, remain)
                cost += use * old_price
                remain -= use
                if not remain:
                    break
            assert not remain
            held = 0 if net > 0 else 1
            delta = Fraction(close, UNIT) * (1 - price - int(held == winner))
            return dict(
                status="valid",
                ts=ts,
                age=ts - group[0]["S"],
                parent=next(iter(parents)),
                roles=sorted({f["role"] for f in group}),
                side=side,
                held=held,
                held_units=abs(net),
                close_units=close,
                first_group_units=qty,
                cash_price=float(price),
                cheapest_pair_cost=float(cost / close + price),
                all_lots_over_one=float(cost / close + price) > 1 + 1e-8,
                delta=float(delta),
                normalized_five_delta=float(
                    Fraction(min(close, 5 * UNIT), UNIT)
                    * (1 - price - int(held == winner))
                ),
                tx=sorted({f["tx"] for f in group}),
            )
        net += sign * sum(f["qty"] for f in group)
        lots += [(f["qty"], Fraction(f["cash_cost"], f["qty"])) for f in group]
    return {"status": "no_reduction", "delta": 0.0, "normalized_five_delta": 0.0}


def summarize_economics(rows):
    valid = [x for x in rows if "delta" in x]
    days = defaultdict(float)
    for x in valid:
        days[day(x["S"])] += x["delta"]
    rng = random.Random(20260922)
    samples = sorted(
        sum(rng.choices(list(days.values()), k=len(days))) for _ in range(10000)
    )
    return dict(
        n=len(valid),
        total_delta=sum(x["delta"] for x in valid),
        ex_top3=sum(
            x["delta"]
            for x in sorted(valid, key=lambda x: x["delta"], reverse=True)[3:]
        ),
        normalized_five_sum=sum(x["normalized_five_delta"] for x in valid),
        by_day=dict(days),
        day_bootstrap95_sum=[samples[250], samples[9750]],
        leave_one_day_out={d: sum(days.values()) - v for d, v in days.items()},
        positive=sum(x["delta"] > 0 for x in valid),
        negative=sum(x["delta"] < 0 for x in valid),
    )


def main():
    # The known seven-row loss of multiplicity is reproduced from fetch chunks.
    hist = DATA / "bosona_gec_20260921"
    windows = read(hist / "windows.json")
    winners = {w["S"]: w["winner"] for w in windows}
    days = defaultdict(list)
    for start in winners:
        days[day(start)].append(start)
    chunks = [read(p) for p in sorted((hist / "activity").glob("*.json"))]
    assert all(c["complete"] for c in chunks)
    assert all(a["end"] + 1 == b["start"] for a, b in zip(chunks, chunks[1:]))
    raw = [
        r
        for c in chunks
        for r in c["rows"]
        if r.get("slug", "").startswith("btc-updown-5m-")
        and int(r["slug"].rsplit("-", 1)[1]) in winners
    ]
    buys = [r for r in raw if r["type"] == "TRADE"]
    assert all(r["side"] == "BUY" for r in buys)
    old = [r for r in read(hist / "activity.json") if r["type"] == "TRADE"]
    lost = Counter(map(key, buys)) - Counter(map(key, old))
    correction = []
    for k, n in lost.items():
        r = next(r for r in buys if key(r) == k)
        start = int(r["slug"].rsplit("-", 1)[1])
        correction.append(
            dict(
                S=start,
                tx=r["transactionHash"],
                multiplicity_lost=n,
                qty=r["size"],
                cash=r["usdcSize"],
                payout=r["size"] if r["outcomeIndex"] == winners[start] else 0,
            )
        )
    payout = sum(
        units(r["size"])
        for r in buys
        if r["outcomeIndex"] == winners[int(r["slug"].rsplit("-", 1)[1])]
    )
    cash = sum(units(r["usdcSize"]) for r in buys)
    assert len(buys) == 19768 and payout - cash == 8313228464
    historical = dict(
        markets=len(winners),
        calendar_slots=(1789943400 - 1789257600) // 300,
        records=len(buys),
        old_records=len(old),
        cash_units=cash,
        payout_units=payout,
        pnl_units=payout - cash,
        real_multiplicity_correction=correction,
        chunk_count=len(chunks),
        activity_types=dict(Counter(r["type"] for r in raw)),
        records_by_day=dict(
            Counter(day(int(r["slug"].rsplit("-", 1)[1])) for r in buys)
        ),
        pre_window_buys=sum(
            r["timestamp"] < int(r["slug"].rsplit("-", 1)[1]) for r in buys
        ),
        after_end_buys=sum(
            r["timestamp"] >= int(r["slug"].rsplit("-", 1)[1]) + 300 for r in buys
        ),
        accounting_basis="Winning-token payout minus API usdcSize; rebates/fixed costs excluded. Full transfer audit only in R1 subset.",
    )

    manifest = read(R1 / "manifest.json")
    expected_hash64 = sorted(
        s
        for ss in days.values()
        for s in sorted(
            ss, key=lambda x: sha256(f"R1-20260921:{x}".encode()).hexdigest()
        )[:8]
    )
    assert expected_hash64 == manifest["cohorts"]["representative"]
    markets, activity, old_report = (
        read(R1 / "markets.json"),
        read(R1 / "activity.json"),
        read(R1 / "report.json"),
    )
    (actor,) = {r["proxyWallet"].lower() for r in activity}
    probe = module(DATA / "btc5m_order_identity_20260921/check.py", "receipt_decoder")
    classifier = module(
        DATA / "g1_selective_exit_20260922/analyze.py", "frozen_classifier"
    )
    classifier.check()
    by_tx = defaultdict(list)
    for r in activity:
        if r["type"] == "TRADE":
            by_tx[r["transactionHash"]].append(r)
    fills, by_start, cash_diffs = [], defaultdict(list), []
    for tx, group in by_tx.items():
        receipt = read(R1 / "receipts" / f"{tx}.json")
        decoded = probe.decode(receipt, actor)
        for f in decoded:
            matches = [r for r in group if r["asset"] == f["token"]]
            assert matches and f["side"] == 0
            start = int(matches[0]["slug"].rsplit("-", 1)[1])
            market = markets[str(start)]
            tokens = json.loads(market["clobTokenIds"])
            assert all(
                r["conditionId"] == market["conditionId"]
                and tokens[r["outcomeIndex"]] == r["asset"]
                for r in matches
            )
            (ts,) = {r["timestamp"] for r in group}
            f.update(
                S=start,
                ts=ts,
                outcome=tokens.index(f["token"]),
                block=int(receipt["blockNumber"], 16),
                transaction_index=int(receipt["transactionIndex"], 16),
            )
            fills.append(f)
            by_start[start].append(f)
        for token in {r["asset"] for r in group}:
            aa, ff = (
                [r for r in group if r["asset"] == token],
                [f for f in decoded if f["token"] == token],
            )
            assert sum(units(r["size"]) for r in aa) == sum(f["qty"] for f in ff)
            diff = sum(units(r["usdcSize"]) for r in aa) - sum(
                f["cash_cost"] for f in ff
            )
            assert abs(diff) <= 10
            cash_diffs.append(diff)
    assert sorted(fills, key=lambda f: (f["tx"], f["log_index"])) == sorted(
        old_report["fills"], key=lambda f: (f["tx"], f["log_index"])
    )
    all_rows, excluded, accounts, firsts = [], [], [], []
    for start, fs in sorted(by_start.items()):
        history = read(R1 / "full_activity" / f"{start}.json")
        assert history["complete"]
        history_buys = [r for r in history["rows"] if r["type"] == "TRADE"]
        subset = [
            r
            for g in by_tx.values()
            for r in g
            if int(r["slug"].rsplit("-", 1)[1]) == start
        ]
        assert Counter(map(key, history_buys)) == Counter(map(key, subset))
        q, cash = [0, 0], 0
        pre, end = None, None
        for r in history["rows"]:
            assert r["type"] in ("TRADE", "MERGE", "REDEEM")
            if r["timestamp"] < start + 300:
                assert r["type"] in ("TRADE", "MERGE")
            if pre is None and r["timestamp"] >= start:
                pre = q.copy()
            if end is None and r["timestamp"] >= start + 300:
                end = q.copy()
            size, usd = units(r["size"]), units(r["usdcSize"])
            if r["type"] == "TRADE":
                assert r["side"] == "BUY"
                q[r["outcomeIndex"]] += size
                cash -= usd
            elif r["type"] == "MERGE":
                q = [v - size for v in q]
                cash += usd
            else:
                q[r["outcomeIndex"]] -= size
                cash += usd
            assert min(q) >= 0
        market = markets[str(start)]
        prices = [Decimal(str(x)) for x in json.loads(market["outcomePrices"])]
        winner = prices.index(Decimal(1))
        expected = sum(
            units(r["size"]) * (r["outcomeIndex"] == winner) - units(r["usdcSize"])
            for r in history_buys
        )
        assert cash + q[winner] == expected
        accounts.append(
            dict(
                S=start,
                winner=winner,
                activity_types=dict(Counter(r["type"] for r in history["rows"])),
                pre_window_units=pre or [0, 0],
                end_window_units=end or q,
                final_token_units=q,
                observed_cash_units=cash,
                terminal_wealth_units=cash + q[winner],
                full_history_fetch_ms=history["fetched_ms"],
                pre_window_buys=sum(r["timestamp"] < start for r in history_buys),
            )
        )
        rr, ee = classifier.classify(fs)
        all_rows += rr
        excluded += ee
        first = dict(S=start, **first_reduction(fs, winner))
        old_first = next(x for x in old_report["market_results"] if x["S"] == start)[
            "first_reduction"
        ]
        assert first["status"] == old_first["status"]
        if first["status"] == "valid":
            assert abs(first["delta"] - old_first["delta"]) < 1e-8
            assert first["all_lots_over_one"] == old_first["all_lot_pair_cost_over_one"]
        firsts.append(first)
    sample = set(expected_hash64)
    rows = [x for x in all_rows if x["S"] in sample]
    excluded64 = [x for x in excluded if x["S"] in sample]
    taker = [x for x in rows if x["role"] == "taker" and x["kind"] == "reduce"]
    assert (
        len(rows) == 262
        and sum(len(x["parents"]) for x in excluded64) == 43
        and len(taker) == 26
    )
    for r in taker:
        parent_fills = [f for f in by_start[r["S"]] if f["order_hash"] == r["parent"]]
        held = abs(r["net_before_units"])
        r.update(
            residual_units=held - r["quantity_units"],
            floor_cent_share_match=r["quantity_units"] == held // 10000 * 10000,
            full_parent_units=sum(f["qty"] for f in parent_fills),
            full_parent_seconds=len({f["ts"] for f in parent_fills}),
            fee_units=sum(f["fee"] for f in parent_fills),
            winner=winners[r["S"]],
        )
        assert (
            r["full_parent_units"] == r["quantity_units"]
            and r["full_parent_seconds"] == 1
        )
        held_wins = (0 if r["net_before_units"] > 0 else 1) == r["winner"]
        r["local_delta"] = (
            r["reducing_units"] / UNIT * (1 - r["cash_price"] - held_wins)
        )
    near_flat_paths = []
    for r in taker:
        if r["closed_fraction"] < 0.99:
            continue
        fs = by_start[r["S"]]
        later = [f for f in fs if r["ts"] < f["ts"] < r["S"] + 300]
        next_ts = min((f["ts"] for f in later), default=None)
        next_group = [f for f in later if f["ts"] == next_ts]
        seen_before = {f["order_hash"] for f in fs if f["ts"] <= r["ts"]}
        held_side = 0 if r["net_before_units"] > 0 else 1
        next_sides = sorted({f["outcome"] for f in next_group})
        near_flat_paths.append(
            dict(
                S=r["S"],
                parent=r["parent"],
                age=r["age"],
                floor_cent_share_match=r["floor_cent_share_match"],
                residual_units=r["residual_units"],
                exact_flat=r["residual_units"] == 0,
                held_side=held_side,
                later_fills=len(later),
                later_new_parents=len({f["order_hash"] for f in later} - seen_before),
                next_delay_seconds=next_ts - r["ts"] if next_ts is not None else None,
                next_sides=next_sides,
                next_group_units=sum(f["qty"] for f in next_group),
                next_group_roles=sorted({f["role"] for f in next_group}),
                next_parents=sorted({f["order_hash"] for f in next_group}),
                next_new_parents=sorted(
                    {f["order_hash"] for f in next_group} - seen_before
                ),
                next_tx=sorted({f["tx"] for f in next_group}),
                later_new_parent_sides=sorted(
                    {f["outcome"] for f in later if f["order_hash"] not in seen_before}
                ),
            )
        )
    # Sensitivity only: each parent's first-second aggregate is kept together.
    # This does not reconstruct placement time or unknown within-parent interleaving.
    ambiguity = []
    for start in sorted(sample):
        seen, net, seconds = set(), 0, defaultdict(list)
        for f in by_start[start]:
            seconds[f["ts"]].append(f)
        for ts, gg in sorted(seconds.items()):
            pp = defaultdict(list)
            for f in gg:
                pp[f["order_hash"]].append(f)
            if len(pp) > 1 or len({f["outcome"] for f in gg}) > 1 or ts >= start + 300:
                assert len(pp) <= 8
                possibilities = defaultdict(set)
                if (
                    all(len({f["outcome"] for f in ff}) == 1 for ff in pp.values())
                    and ts < start + 300
                ):
                    for seq in permutations(pp):
                        n = net
                        for p in seq:
                            signed = sum(
                                (1 if f["outcome"] == 0 else -1) * f["qty"]
                                for f in pp[p]
                            )
                            possibilities[p].add(action(n, signed))
                            n += signed
                for p in sorted(pp.keys() - seen):
                    ambiguity.append(
                        dict(
                            S=start,
                            ts=ts,
                            age=ts - start,
                            parent=p,
                            roles=sorted({f["role"] for f in pp[p]}),
                            possible_kinds=sorted(possibilities[p]),
                            before_units=net,
                            tx=sorted({f["tx"] for f in pp[p]}),
                        )
                    )
            net += sum((1 if f["outcome"] == 0 else -1) * f["qty"] for f in gg)
            seen.update(pp)
    first64 = [x for x in firsts if x["S"] in sample]
    first15 = [x for x in first64 if x.get("roles") == ["taker"]]
    assert len(first15) == 15 and sum(x["all_lots_over_one"] for x in first15) == 10
    frozen_selective = read(DATA / "g1_selective_exit_20260922/results.json")
    old_keys = {(r["S"], r["parent"], r["ts"]): r for r in frozen_selective["rows"]}
    assert all(
        all(
            r[k] == old_keys[r["S"], r["parent"], r["ts"]][k]
            for k in ("kind", "quantity_units", "net_before_units", "role")
        )
        for r in all_rows
    )
    cases = []
    case_selection = {
        1789456200: "Largest beneficial first taker reduction in hash64; diagnostic selection after outcomes.",
        1789924800: "Largest harmful first taker reduction in hash64; diagnostic selection after outcomes.",
        1789580400: "Largest winning no-observed-reduction market in hash64; diagnostic selection after outcomes.",
        1789739700: "Largest losing no-observed-reduction market in hash64; diagnostic selection after outcomes.",
        1789468500: "Exact-flat 21-share taker close followed nine seconds later by a distinct 148-share taker parent.",
    }
    for start, why in case_selection.items():
        account = next(a for a in accounts if a["S"] == start)
        cases.append(
            dict(
                S=start,
                selection=why,
                account=account,
                first_reduction=next(r for r in firsts if r["S"] == start),
                fills=sorted(
                    by_start[start], key=lambda f: (f["ts"], f["tx"], f["log_index"])
                ),
            )
        )
    # Validate frozen input integrity in addition to recomputing decoded quantities.
    for name, digest in manifest["input_sha256"].items():
        assert sha256((R1 / name).read_bytes()).hexdigest() == digest
    fetch = read(R1 / "fetch_manifest.json")
    for name, digest in fetch["files"].items():
        assert sha256((R1 / name).read_bytes()).hexdigest() == digest
    result = dict(
        mode="OFFLINE_NO_NETWORK_NO_ORDERS",
        historical=historical,
        receipt_audit=dict(
            markets=len(by_start),
            api_buys=sum(map(len, by_tx.values())),
            transactions=len(by_tx),
            decoded_fills=len(fills),
            parents=len({f["order_hash"] for f in fills}),
            shares_units=sum(f["qty"] for f in fills),
            cash_units=sum(f["cash_cost"] for f in fills),
            fee_units=sum(f["fee"] for f in fills),
            api_minus_chain_cash_units=sum(cash_diffs),
            max_transaction_cash_difference_units=max(map(abs, cash_diffs)),
            all_receipts_redecoded_and_transfer_reconciled=True,
            complete_activity_types=dict(
                sum((Counter(a["activity_types"]) for a in accounts), Counter())
            ),
            pre_window_markets=sum(any(a["pre_window_units"]) for a in accounts),
            pre_window_buys=sum(a["pre_window_buys"] for a in accounts),
            caveat="Full API history is not proof of zero initial onchain balance or absence of external transfers; MERGE/REDEEM receipts not independently audited.",
        ),
        hash64=dict(
            markets=64,
            all_parents=305,
            classified=262,
            excluded=43,
            roles=dict(Counter(r["role"] for r in rows)),
            kinds_by_role={
                role: dict(Counter(r["kind"] for r in rows if r["role"] == role))
                for role in sorted({r["role"] for r in rows})
            },
            taker_reductions=26,
            reducing_markets=len({r["S"] for r in taker}),
            floor_cent_share_matches=sum(r["floor_cent_share_match"] for r in taker),
            near_flat99=sum(r["closed_fraction"] >= 0.99 for r in taker),
            median_closed_fraction=median(r["closed_fraction"] for r in taker),
            median_age=median(r["age"] for r in taker),
            age_range=[min(r["age"] for r in taker), max(r["age"] for r in taker)],
            median_cash_price=median(r["cash_price"] for r in taker),
            by_day=dict(Counter(day(r["S"]) for r in taker)),
            local_deltas_sum_not_a_policy_pnl=sum(r["local_delta"] for r in taker),
            taker_ambiguity=[r for r in ambiguity if r["roles"] == ["taker"]],
            first_reduction_status=dict(Counter(x["status"] for x in first64)),
        ),
        near_flat_paths=near_flat_paths,
        diagnostic_cases=cases,
        strict_maker_reverse_sensitivity=dict(
            total=sum(r["role"] == "maker" and r["kind"] == "reverse" for r in rows),
            pre_net_below_cent_share=sum(
                r["role"] == "maker"
                and r["kind"] == "reverse"
                and abs(r["net_before_units"]) < 10000
                for r in rows
            ),
            pre_net_below_five_shares=sum(
                r["role"] == "maker"
                and r["kind"] == "reverse"
                and abs(r["net_before_units"]) < 5 * UNIT
                for r in rows
            ),
            note="Descriptive sensitivity only; strict integer classifier unchanged.",
        ),
        first15_economics=summarize_economics(first15),
        first55_economics=summarize_economics(first64),
        taker_reduction_rows=taker,
        first64_rows=first64,
        first15_rows=first15,
        ambiguous_parent_rows=ambiguity,
        all_classified_rows=all_rows,
        full_activity_accounts=accounts,
        source_sha256=INPUTS,
        code_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    (OUT / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "receipt_audit",
                    "hash64",
                    "first15_economics",
                    "first55_economics",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    assert (
        action(5, -5) == "reduce"
        and action(5, -6) == "reverse"
        and action(0, 1) == "open"
    )
    assert units("0.000001") == 1
    test_fills = [
        dict(
            S=0,
            ts=10,
            outcome=0,
            qty=5 * UNIT,
            cash_cost=3 * UNIT,
            order_hash="open",
            role="maker",
            tx="a",
        ),
        dict(
            S=0,
            ts=20,
            outcome=1,
            qty=5 * UNIT,
            cash_cost=3 * UNIT,
            order_hash="close",
            role="taker",
            tx="b",
        ),
    ]
    assert first_reduction(test_fills, 0)["delta"] == -3
    assert first_reduction(test_fills, 1)["delta"] == 2
    assert first_reduction(test_fills, 0)["all_lots_over_one"]
    main()
