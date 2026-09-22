"""SDK sinirinda gozlem: saatler yereldir, exchange saati degildir."""
import atexit
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import threading
import time
import uuid

aktif = None


def saat():
    return {'utc_ns': time.time_ns(), 'mono_ns': time.monotonic_ns()}


def kimlik(value):
    return value if isinstance(value, str) and re.fullmatch(r'0x[0-9a-fA-F]{64}|[0-9]{1,80}', value) else None


def sayi(value):
    try:
        n = float(value)
        return n if math.isfinite(n) and n >= 0 else None
    except (ValueError, TypeError, OverflowError):
        return None


def emir(oi, token, price, size):
    return dict(oi=oi if oi in (0, 1) else None, token=kimlik(str(token)),
                price=sayi(price), size=sayi(size))


def ozet(op, result, meta):
    # Yanit/istisna metni ve imzali POST govdesi gunluge girmez.
    def order(r):
        r = r if isinstance(r, dict) else {}
        status = r.get('status')
        status = status.upper() if isinstance(status, str) else None
        return dict(oid=kimlik(r.get('orderID') or r.get('orderId') or r.get('id')),
                    token=kimlik(r.get('asset_id') or r.get('token_id')),
                    price=sayi(r.get('price')), size=sayi(r.get('original_size')),
                    matched=sayi(r.get('size_matched')),
                    status=status if status in ('LIVE', 'MATCHED', 'CANCELED', 'CANCELLED',
                                                'DELAYED', 'UNMATCHED', 'INVALID') else None,
                    success=r.get('success') if isinstance(r.get('success'), bool) else None)

    if op in ('post_batch', 'open_orders'):
        reply = {'items': [order(r) for r in result] if isinstance(result, list) else None}
        if op == 'post_batch':
            reply['slots_match'] = (isinstance(result, list)
                                    and len(result) == len(meta.get('orders', []))
                                    and all(isinstance(r, dict) for r in result))
        return reply
    if op in ('post', 'get_order'):
        return order(result)
    if op in ('cancel', 'cancel_batch'):
        r = result if isinstance(result, dict) else {}
        yes, no = r.get('canceled'), r.get('not_canceled')
        return {'items': [dict(oid=oid,
                               canceled=(oid in yes) if isinstance(yes, list) else None,
                               not_canceled=(oid in no) if isinstance(no, dict) else None)
                          for oid in meta['oids']]}
    raise ValueError('unknown telemetry operation')


class Gunluk:
    def __init__(self, path, mode, source):
        self.path = Path(path)
        self.session = uuid.uuid4().hex
        self.lock = threading.Lock()
        self.seq = self.errors = 0
        hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (Path(source), Path(__file__))}
        self.yaz('session_start', mode=mode, sources=hashes)

    def ariza(self):
        self.errors += 1
        if self.errors == 1:
            try:
                sys.stderr.write('EMIR_IZ_ARIZA: bu oturum kalibrasyon icin gecersiz.\n')
            except Exception:
                pass

    def yaz(self, event, **fields):
        try:
            # ponytail: kisa dosya kilidi; ag cagrisi kilidin disinda kalir.
            with self.lock:
                self.seq += 1
                row = dict(schema=1, session=self.session, pid=os.getpid(), seq=self.seq,
                           event=event, errors=self.errors, **saat(), **fields)
                with self.path.open('a', encoding='utf-8') as f:
                    f.write(json.dumps(row, allow_nan=False, separators=(',', ':')) + '\n')
        except Exception:
            self.ariza()


def baslat(path, mode, source):
    global aktif
    aktif = Gunluk(path, mode, source)
    atexit.register(aktif.yaz, 'session_end')
    return aktif


def cagir(op, meta, fn, *args, **kwargs):
    g = aktif
    if g is None:
        return fn(*args, **kwargs)
    attempt = uuid.uuid4().hex
    g.yaz('request', attempt=attempt, op=op, meta=meta)
    begin = saat()  # Dosyayi yazma suresi SDK gecikmesine dahil degil.
    try:
        result = fn(*args, **kwargs)
    except BaseException as ex:
        end = saat()
        g.yaz('error', attempt=attempt, op=op, begin=begin, end=end,
              duration_ns=end['mono_ns']-begin['mono_ns'], error_type=type(ex).__name__)
        raise
    end = saat()
    try:
        g.yaz('response', attempt=attempt, op=op, begin=begin, end=end,
              duration_ns=end['mono_ns']-begin['mono_ns'], reply=ozet(op, result, meta))
    except Exception:
        g.ariza()  # Kabul edilmis POST cevabi gozlem hatasi yuzunden kaybolamaz.
    return result


def dolum(oid, delta, total, source):
    if aktif is not None:
        aktif.yaz('fill_observed', oid=kimlik(oid), delta=sayi(delta), total=sayi(total),
                  source=source, exchange_ns=None)
