"""Verify the BTC15 review packet offline; never import trading code."""
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    manifest = read("manifest.json")
    for row in manifest["files"]:
        path = ROOT / row["path"]
        assert path.resolve().is_relative_to(ROOT), row["path"]
        assert not path.is_symlink(), row["path"]
        data = path.read_bytes()
        assert len(data) == row["bytes"], row["path"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"], row["path"]
    folder = "R/btc15_reconciled_v1_20260921/results/"
    fills = [r for r in read(folder + "fills.json") if r["group"] == "btc_15m"]
    table = read(folder + "reconciliation.json")
    assert len(fills) == 5441
    assert len({r["condition_id"] for r in fills}) == 598
    assert Counter(r["role"] for r in fills) == {"maker": 4387, "taker": 1054}
    total = Decimal(0)
    for row in fills:
        payout = Decimal(row["qty"]) if row["side"] == row["winner"] else Decimal(0)
        pnl = payout - Decimal(row["cash"])
        assert pnl == Decimal(row["pnl"])
        total += pnl
    expected = sum(Decimal(x["pnl"]) for x in table["groups"]["btc_15m"].values())
    assert total == expected
    late = [r for r in fills if r["phase"] == "add" and 600 <= r["age"] < 900]
    assert len(late) == 1150
    for role in ("ALL", "maker", "taker"):
        rows = [r for r in late if role == "ALL" or r["role"] == role]
        by_market = defaultdict(Decimal)
        for row in rows:
            by_market[row["condition_id"]] += Decimal(row["pnl"])
        result = table["late"][role]
        assert len(rows) == result["fills"]
        assert len(by_market) == result["markets"]
        assert sum(by_market.values()) == Decimal(result["pnl"])
        assert sum(sorted(by_market.values(), reverse=True)[10:]) == Decimal(result["ex_top10"])
    latest = read("R/btc15_transport_v2_20260922/results/summary.json")
    assert latest["assigned"] == 8 and latest["eligible"] == 6
    assert latest["economic_pnl"] is None
    print(f"PASS: {len(manifest['files'])} artifact hashes; BTC15 598 markets / 5441 fills; cash contribution {total}; corrected late-addition totals; economic PnL remains unvalidated.")


if __name__ == "__main__":
    main()
