#!/usr/bin/env python3
"""Resume-safe Telonex downloader: all Polymarket btc-updown-5m markets, 2026-08-14..2026-09-02.

One asset per market (asset_id_0 = Up); a single asset file carries every fill of the market
(verified: sibling files overlap 100% on (tx_hash, log_index)). Days per market come from the
catalog channel coverage [<channel>_from, <channel>_to).
"""
from __future__ import annotations

import argparse, concurrent.futures, datetime as dt, hashlib, os, sqlite3, threading, time
from pathlib import Path

import duckdb, pandas as pd, pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CATALOG = REPO / "datasets/polymarket_markets.parquet"
OUT = REPO / "data/parquet/telonex_pm_btc5m_actor_hunt_20260814_20260902"
DENSA = REPO / "data/parquet/telonex_densa_twap60_actor_20260828_v1"
STATE = HERE / "TELONEX_DOWNLOAD_STATE.sqlite3"
WINDOW_START = dt.datetime(2026, 8, 14, tzinfo=dt.timezone.utc)
WINDOW_END = dt.datetime(2026, 9, 3, tzinfo=dt.timezone.utc)
DAY_MIN, DAY_MAX = dt.date(2026, 8, 13), dt.date(2026, 9, 3)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def valid_parquet(path: Path) -> bool:
    try:
        return path.exists() and path.stat().st_size > 0 and pq.read_metadata(path).num_rows >= 0
    except Exception:
        return False


def fname(channel: str, day: str, asset: str) -> str:
    return f"polymarket_{channel}_{day}_{asset}.parquet"


def universe() -> pd.DataFrame:
    con = duckdb.connect()
    df = con.execute(
        """select slug, market_id, asset_id_0, asset_id_1, result_id, status,
                  onchain_fills_from, onchain_fills_to, trades_from, trades_to,
                  book_snapshot_5_from, book_snapshot_5_to
           from read_parquet(?) where exchange='polymarket' and slug like 'btc-updown-5m-%'""",
        [str(CATALOG)],
    ).fetchdf()
    con.close()
    df["ts"] = df.slug.str.extract(r"(\d+)$").astype("int64")
    df["start"] = pd.to_datetime(df.ts, unit="s", utc=True)
    df = df[(df.start >= WINDOW_START) & (df.start < WINDOW_END)].sort_values("ts").reset_index(drop=True)
    return df


def build_tasks(channel: str) -> list[dict]:
    df = universe()
    tasks = []
    for r in df.itertuples(index=False):
        a = pd.to_datetime(getattr(r, f"{channel}_from"), errors="coerce")
        b = pd.to_datetime(getattr(r, f"{channel}_to"), errors="coerce")
        if pd.isna(a) or pd.isna(b):
            continue
        d = max(a.date(), DAY_MIN)
        while d < min(b.date(), DAY_MAX + dt.timedelta(days=1)):
            tasks.append({"task_id": f"{channel}|{d.isoformat()}|{r.market_id}", "channel": channel,
                          "day": d.isoformat(), "market_id": r.market_id, "slug": r.slug,
                          "asset0": str(r.asset_id_0), "asset1": str(r.asset_id_1)})
            d += dt.timedelta(days=1)
    return tasks


def open_state() -> sqlite3.Connection:
    con = sqlite3.connect(STATE, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS tasks (task_id TEXT PRIMARY KEY, channel TEXT, day TEXT,
        market_id TEXT, slug TEXT, asset TEXT, status TEXT, path TEXT, rows INTEGER, bytes INTEGER,
        sha256 TEXT, error TEXT, updated_at TEXT)""")
    con.commit()
    return con


def redact(exc: Exception) -> str:
    m = f"{type(exc).__name__}:{exc}"
    k = os.environ.get("TELONEX_KEY", "")
    return (m.replace(k, "<redacted>") if k else m)[:500]


def download_one(t: dict, key: str) -> tuple:
    ch, day = t["channel"], t["day"]
    # shared densa file (either asset) for the same day/channel?
    for a in (t["asset0"], t["asset1"]):
        p = DENSA / ch / fname(ch, day, a)
        if valid_parquet(p):
            md = pq.read_metadata(p)
            return "shared", a, str(p), md.num_rows, p.stat().st_size, sha256(p), ""
    a = t["asset0"]
    target = OUT / ch / fname(ch, day, a)
    if valid_parquet(target):
        md = pq.read_metadata(target)
        return "downloaded", a, str(target), md.num_rows, target.stat().st_size, sha256(target), ""
    target.parent.mkdir(parents=True, exist_ok=True)
    nxt = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
    try:
        import telonex
        files = telonex.download(api_key=key, exchange="polymarket", channel=ch, from_date=day, to_date=nxt,
                                 asset_id=a, download_dir=str(target.parent), timeout=180, concurrency=1, verbose=False)
        if not files:
            return "not_found", a, str(target), 0, 0, "", ""
        actual = Path(files[0])
        if actual.resolve() != target.resolve():
            actual.replace(target)
        if not valid_parquet(target):
            raise ValueError("invalid parquet after download")
        md = pq.read_metadata(target)
        return "downloaded", a, str(target), md.num_rows, target.stat().st_size, sha256(target), ""
    except Exception as exc:  # noqa
        return "error", a, str(target), 0, 0, "", redact(exc)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="onchain_fills")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--max-tasks", type=int, default=0)
    ap.add_argument("--retry-errors", action="store_true")
    args = ap.parse_args()
    key = os.environ.get("TELONEX_KEY", "")
    if not key:
        raise SystemExit("TELONEX_KEY required")
    tasks = build_tasks(args.channel)
    con = open_state()
    done = {r[0]: r[1] for r in con.execute("select task_id, status from tasks").fetchall()}
    skip = {"downloaded", "shared", "not_found"} if not args.retry_errors else {"downloaded", "shared", "not_found"}
    todo = [t for t in tasks if done.get(t["task_id"]) not in skip]
    if args.max_tasks:
        todo = todo[: args.max_tasks]
    print(f"channel={args.channel} tasks={len(tasks)} todo={len(todo)} already={len(tasks)-len(todo)}", flush=True)
    lock = threading.Lock()
    counts: dict[str, int] = {}
    t0 = time.time()

    def work(t):
        res = download_one(t, key)
        status, asset, path, rows, nbytes, digest, err = res
        with lock:
            con.execute("INSERT OR REPLACE INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (t["task_id"], t["channel"], t["day"], t["market_id"], t["slug"], asset, status, path,
                         rows, nbytes, digest, err, dt.datetime.now(dt.timezone.utc).isoformat()))
            con.commit()
            counts[status] = counts.get(status, 0) + 1
            n = sum(counts.values())
            if n % 50 == 0 or status == "error":
                print(f"[{time.time()-t0:7.0f}s] {n}/{len(todo)} {counts} last={t['slug']} {status} {err[:120]}", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(work, todo))
    print(f"DONE {counts} in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
