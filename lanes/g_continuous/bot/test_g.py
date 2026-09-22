"""G policy plus real reservation/reconciliation paths; no credentials or network."""

import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch

import g_policy as g


def load():
    path = Path(__file__).with_name("ab.py")
    spec = importlib.util.spec_from_file_location("g_test_engine", path)
    b = importlib.util.module_from_spec(spec)
    with patch.object(sys, "argv", [str(path), "--lane-g"]):
        spec.loader.exec_module(b)
    return b


def order(oi, p, q=5, status="dolu", oid=""):
    return dict(
        oi=oi,
        p=p,
        pay=q,
        boy=5,
        durum=status,
        oid=oid,
        ofset=p,
        hedef_ofset=p,
        bb=p,
        dolumlar=[dict(q=q, p=p, ms=1)] if q else [],
    )


def main():
    b = load()
    assert b.LANE == "G" and b.LANE_F and not b.LIVE and b.C_CIFT_TAVAN is None
    assert b.LOG.endswith("LOG_g_kuru.jsonl") and b.STOP.endswith("STOP_G_KURU")
    assert b.iptal_yorumla(
        "test", {"not_canceled": {"test": "PRIVATE_TEST_CANARY"}}
    ) == (False, "borsa_iptal_reddi")
    assert g.target(0.74, 0.75, 0.01, 0, 0) == 0.73
    assert g.target(0.263, 0.264, 0.001, 0, 0) == 0.253
    assert g.target(0.02, 0.03, 0.01, 0, 0) == 0.01
    assert g.target(0.74, 0.75, 0.01, 5, 0) == 0.73
    assert g.target(0.74, 0.75, 0.01, 10, 0) is None
    assert g.target(0.74, 0.75, 0.01, 0, 5) == 0.73
    for args in (
        (None, 0.75, 0.01, 0, 0),
        (0.75, 0.74, 0.01, 0, 0),
        (0.74, 0.75, None, 0, 0),
        (0.74, 0.75, 0.1, 0, 0),
    ):
        assert g.target(*args) is None
    now = round(time.time() * 1000)
    S = now / 1000 - 60
    signal = dict(
        S=S, karar_ms=now, book_ms=now, model_sha=g.SHA, bb=0.74, ba=0.75, tick=0.01
    )
    empty = dict(emir=[], klip=5, cozuldu=False, kol="G")
    held = {**empty, "emir": [order(1, 0.8)]}
    assert g.quality(empty, 0, 0.73, signal, now) == (True, "open")
    assert g.quality(held, 0, 0.73, signal, now) == (
        True,
        "reduce",
    )  # >$1 pair allowed, bounded by exposure.
    for changed in (
        {"book_ms": now - 3001},
        {"book_ms": now + 1},
        {"karar_ms": now - 1501},
        {"model_sha": "bad"},
        {"ba": None},
    ):
        assert not g.quality(held, 0, 0.73, {**signal, **changed}, now)[0]
    late = {**signal, "S": now / 1000 - 250}
    assert (
        not g.quality(empty, 0, 0.73, late, now)[0]
        and g.quality(held, 0, 0.73, late, now)[0]
    )
    assert not g.quality(held, 0, 0.73, {**signal, "S": now / 1000 - 290}, now)[0]
    paired = {**empty, "emir": [order(0, 0.2), order(1, 0.7)]}
    assert not g.quality(paired, 0, 0.73, late, now)[0]  # Reopening is new risk.
    for q0, q1 in itertools.product((0, 2, 5), repeat=2):
        w = {
            **empty,
            "emir": [
                order(0, 0.4, q0),
                order(1, 0.5, q1),
                order(0, 0.6, 0, "acik"),
                order(1, 0.3, 0, "belirsiz"),
            ],
        }
        expected = max(
            0,
            max(
                0.4 * q0
                + 0.5 * q1
                + 3 * f0
                + 1.5 * f1
                - (q0 + 5 * f0 if winner == 0 else q1 + 5 * f1)
                for winner, f0, f1 in itertools.product((0, 1), repeat=3)
            ),
        )
        assert abs(b.pencere_risk(w) - expected) < 1e-9
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        b.STATE = str(root / "state")
        b.LOG = str(root / "log")
        b.STOP = str(root / "STOP")
        b.log = lambda *args, **kw: None
        b.pen = {("btc", int(S)): copy.deepcopy(held)}
        w = b.pen[("btc", int(S))]
        calls = []
        b.koy_toplu = lambda args: calls.append(args) or [(0, 0.73, "mock", "KABUL")]
        r = b.d_koy(("btc", int(S)), w, 0, "up", 0.73, 5, 0.74, 0.75, 100, signal)
        assert r and len(calls) == 1 and b.d_miktar(w, 0) == 0
        assert (
            b.d_koy(("btc", int(S)), w, 0, "up", 0.73, 5, 0.74, 0.75, 100, signal)
            is None
        )
        assert abs(b.toplam_risk() - 4) < 1e-9
        b.pay_ekle(r, 5, "test", ("btc", int(S)))
        b.pay_ekle(r, 5, "test_repeat", ("btc", int(S)))
        assert len(r["dolumlar"]) == 1 and abs(b.toplam_risk() - 2.65) < 1e-9
        assert b.pencere_hesabi(w, 0)["pnl"] == b.pencere_hesabi(w, 1)["pnl"]
        # Partial completion below exchange minimum cannot overshoot net inventory.
        partial = {**empty, "emir": [order(1, 0.8), order(0, 0.73, 2)]}
        b.pen = {("btc", int(S)): partial}
        assert b.d_miktar(partial, 0) == 3
        assert (
            b.d_koy(("btc", int(S)), partial, 0, "up", 0.73, 5, 0.74, 0.75, 100, signal)
            is None
        )
        b.st["pnl"] = b.st["pnl_yerel"] = -9
        w = copy.deepcopy(empty)
        b.pen = {("btc", int(S)): w}
        assert (
            b.d_koy(("btc", int(S)), w, 0, "up", 0.73, 5, 0.74, 0.75, 100, signal)
            is None
        )
        b.st["pnl"] = b.st["pnl_yerel"] = 0
        with (
            patch.object(b, "healthy", return_value=True, create=True),
            patch.object(b.emir_iz, "aktif", SimpleNamespace(errors=1)),
        ):
            b.LIVE = b.MUTABAKAT_OK = True
            assert (
                b.d_koy(("btc", int(S)), w, 0, "up", 0.73, 5, 0.74, 0.75, 100, signal)
                is None
            )
            b.LIVE = False
        (root / "STOP").touch()
        assert (
            b.d_koy(("btc", int(S)), w, 0, "up", 0.73, 5, 0.74, 0.75, 100, signal)
            is None
        )
        # Missing order details stay unknown; no invented zero fill or freed reserve.
        b.iptal = lambda oid: (True, "zaten_yok")
        b.dolum_oku = lambda oid: (None, "")
        r = order(0, 0.73, 0, "acik", "unknown")
        assert not b.kapat(r, "test") and r["durum"] == "belirsiz"
        b.dolum_oku = lambda oid: (5, "MATCHED")
        assert b.kapat(r, "test") and r["pay"] == 5
    # Raw same-looking trades remain two; an overlapping page is explicitly ambiguous.
    row = dict(
        transactionHash="tx",
        asset="token",
        outcomeIndex=0,
        side="BUY",
        size=5,
        price=0.4,
    )
    ledger = []
    g.append_page(ledger, [row, row], b.islem_anahtari)
    assert len(ledger) == 2
    try:
        g.append_page(ledger, [row], b.islem_anahtari)
    except ValueError:
        pass
    else:
        raise AssertionError("ambiguous page accepted")
    # Real reconciliation, no mocks of its accounting logic; only IO is replaced.
    S = 1
    slug = "btc-updown-5m-1"
    rows = [dict(row, slug=slug, timestamp=2)] * 2
    b.LIVE = True
    b.pen = {}
    b.st["pencereler"] = [["btc", S]]
    b.st["gorulen_tx"] = []
    b.st["gorulen_islem"] = []
    b.st["gorulen_cokluk"] = {}
    b.st["mutabakat_pencere"] = 0
    b.adres = lambda: "public_test"
    b.resmi_sonuc = lambda *args: 0
    b.jget = lambda *args: rows
    with patch.object(b.time, "sleep", lambda _: None):
        assert b.mutabakat() == 6 and b.st["gorulen_cokluk"][b.islem_anahtari(row)] == 2
        rows = rows[:1]
        assert b.mutabakat() is None and b.st["pnl"] == 6 and not b.MUTABAKAT_OK
    assert json.loads(json.dumps(b.st))["gorulen_cokluk"]
    print(
        "G checks passed: policy, real reservation/risk, partial/repeated fill, STOP, unknown cancel, multiset reconciliation"
    )


if __name__ == "__main__":
    main()
