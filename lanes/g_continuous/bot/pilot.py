"""G: varsayilan salt-okunur kontrol; --live yalniz operator baslatmasi."""
import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import io
import json
import logging
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit
from g_guard import REQUIRED


class CheckFailed(ValueError):
    pass


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    manifest = json.loads((root/'G_RELEASE.json').read_text())
    if not REQUIRED <= set(manifest):
        raise CheckFailed('G kaynak listesi eksik')
    for name, digest in manifest.items():
        if sha(root/name) != digest:
            raise CheckFailed('Kaynak hash farki: '+name)
    protocol = json.loads((root/'protocol.json').read_text())
    if (protocol['minutes'], protocol['loss_limit'], protocol['clip'], protocol.get('continuous')) != (None, 10, 5, True):
        raise CheckFailed('Beklenmeyen pilot sinirlari')
    return protocol


def writers():
    found = []
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            if int(proc.name) in (os.getpid(), os.getppid()):
                continue
            args = (proc/'cmdline').read_bytes().decode('utf8', 'ignore').split('\0')
            if args and 'python' in args[0] and '--live' in args:
                cwd = os.readlink(proc/'cwd')
                if any('polymarket-bosona' in str(Path(cwd)/a) for a in args[1:] if a.endswith('.py')):
                    found.append(int(proc.name))
        except OSError:
            pass
    return found


class ReadOnly:
    def __init__(self, client):
        self.client = client

    def __getattr__(self, name):
        if name not in ('get_open_orders', 'get_order', '_get', '_l2_headers', 'host', 'funder'):
            raise RuntimeError('Salt okunur SDK: '+name)
        return getattr(self.client, name)


def preflight(root, protocol):
    if writers():
        raise CheckFailed('Baska LIVE yazici var')
    origin = Path(protocol['source_bot'])
    if sha(origin/protocol.get('source_state','STATE_f.json')) != protocol['source_state_sha']:
        raise CheckFailed('Eski hesap degismis; yeniden inceleme gerekli')
    spec = importlib.util.spec_from_file_location('g_checked_bot', root/'ab.py')
    b = importlib.util.module_from_spec(spec)
    saved = sys.argv
    try:
        sys.argv = [str(root/'ab.py'), '--lane-g']
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(b)  # --live yok: SDK/kimlik kurulmaz.
    finally:
        sys.argv = saved
    assert b.LANE_F and b.KLIP == 5 and not b.LIVE
    # Sirlar yalniz SDK kimlik dogrulamasinda kullanilir, ciktiya yazilmaz.
    from py_clob_client_v2.client import ClobClient
    env = {}
    for line in Path(b.CRED).read_text().splitlines():
        if re.match(r'^\s*[A-Za-z_][A-Za-z_0-9]*=', line):
            key, value = line.split('=', 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    client = ClobClient(env.get('PM_CLOB_HOST', 'https://clob.polymarket.com'), chain_id=137,
                       key=env['PM_PRIVATE_KEY'], signature_type=2, funder=env['PM_FUNDER'])
    client.set_api_creds(client.derive_api_key())
    b.client = ReadOnly(client)
    b.adres = lambda: env['PM_FUNDER'].lower()
    b.LIVE = True  # Yalniz hesap okuma/arsiv mutabakati; emir metodlari yasak.
    b.STATE, b.LOG = str(origin/protocol.get('source_state','STATE_f.json')), str(origin/protocol.get('source_log','LOG_f.jsonl'))
    b.state_kaydet = lambda: None  # Orijinal veya pilot state'i yazilmaz.
    events = []
    b.log = lambda event, **kw: events.append({'event': event, **{
        k: v for k, v in kw.items() if k in ('S', 'pnl', 'pay', 'maliyet', 'duzeltme', 'hata')}})
    read = b.jget

    def checked_get(url, *args):
        for attempt in range(3):
            try:
                data = read(url, *args)
                break
            except Exception as ex:
                events.append(dict(event='READ_FAILED', endpoint=urlsplit(url).path,
                                   error_type=type(ex).__name__, http_status=getattr(ex, 'code', None)))
                if attempt == 2:
                    raise
                time.sleep(3*(attempt+1))
        if not isinstance(data, list):
            raise CheckFailed('Eksik kamu veri cevabi')
        return data

    b.jget = checked_get
    g = b.emir_iz.Gunluk(root/'preflight_emir_iz.jsonl', 'READ_ONLY', root/'ab.py')
    b.emir_iz.aktif = g
    try:
        if b.acik_emirler() != []:
            raise CheckFailed('Acik emir var veya okunamadi')
        b.state_yukle()
        before = b.st['pnl_yerel']
        for key, window in b.pen.items():
            if not window.get('cozuldu'):
                b.cozumle(key, window)
        if any(not w.get('cozuldu') for w in b.pen.values()):
            raise CheckFailed('Eski pencere teyitsiz')
        if b.acilis_maruziyeti() != 0 or b.mutabakat() is None:
            raise CheckFailed('Hesap mutabakati veya dis risk')
        if (not all(math.isfinite(b.st[k]) for k in ('pnl', 'pnl_yerel'))
                or abs(b.st['pnl']-b.st['pnl_yerel']) > .0002 or b.toplam_risk() != 0):
            raise CheckFailed('PnL/risk farki')
        if any(o.get('durum') not in ('kapali', 'dolu') or o.get('gonderiliyor')
               for w in b.pen.values() for o in w['emir']):
            raise CheckFailed('Eski emir teyitsiz')
        if b.acik_emirler() != [] or writers():
            raise CheckFailed('Kontrol sirasinda yeni emir/yazici')
        # G uses executable market books, not the former F probability model.
        # No unused oracle requirement may silently filter its entry universe.
        now = time.time()*1000
        ages = {}
        if g.errors:
            raise CheckFailed('Telemetri yazilamadi')
        state = {'st': b.st, 'pen': {f'{s}|{S}': w for (s, S), w in b.pen.items()}}
        proof = dict(checked_ms=round(now), previous_pnl=before, pnl=b.st['pnl_yerel'],
                     windows=len(b.pen), orders=b.st['emir'], open_orders=0, risk=0,
                     prices_ages_ms=ages, events=events, source_state_sha=protocol['source_state_sha'])
        return state, proof
    finally:
        g.yaz('session_end')
        b.emir_iz.aktif = None
        (root/'preflight_events.json').write_text(json.dumps(events, indent=2)+'\n')


def activate_files(root, state, proof, now):
    """Yalniz operator --live yolunda; testler gecici dizinde cagirir."""
    from f_budget import budget_id
    if any((root/n).exists() for n in ('RUN_G.json', 'STATE_g.json', 'BUDGET_G.json', 'LOG_g.jsonl')):
        raise CheckFailed('Pilot daha once hazirlanmis; butce/sure sifirlanamaz')
    if not (root/'STOP_G').exists():
        raise CheckFailed('Park dosyasi eksik')
    if not all(math.isfinite(state['st'][k]) for k in ('pnl', 'pnl_yerel')):
        raise CheckFailed('Gecersiz PnL')
    anchor = min(state['st']['pnl'], state['st']['pnl_yerel'])
    if not 0 <= now-proof['checked_ms'] <= 30000:
        raise CheckFailed('Eski veya gecersiz onkontrol')
    budget = dict(limit=10, anchor=anchor, cutoff=anchor-10, end_ms=None, continuous=True,
                  created_ms=now, previous_stop=state['st'].get('durdu'))
    budget['id'] = budget_id(budget)
    # Ilk isaret exclusive: yarim hazirlik bile yeniden $10 acamaz.
    with (root/'RUN_G.json').open('x') as f:
        json.dump(dict(proof=proof, budget=budget), f, indent=2)
    state = {**state, 'st': {**state['st'], 'f_budget_id': budget['id'], 'durdu': None}}
    for name, data in [('BUDGET_G.json', budget), ('STATE_g.json', state)]:
        with (root/name).open('x') as f:
            json.dump(data, f)
    (root/'STOP_G').rename(root/'STOP_G.operator_once')
    return budget


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--resume', action='store_true', help='same activated budget; never reset its anchor')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    logging.disable(logging.CRITICAL)
    with (root/'.g_operator.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        protocol = verify(root)
        if (root/'RUN_G.json').exists() and not args.resume:
            raise CheckFailed('Bu pilot tek kullanimlik; yeniden baslatilamaz')
        budget = None
        if args.resume:
            from f_budget import read_budget
            from g_guard import verify as verify_active
            budget = read_budget(root/'BUDGET_G.json', allow_unlimited=True)
            verify_active(root, budget)
            protocol = {**protocol, 'source_bot': str(root), 'source_state': 'STATE_g.json',
                        'source_log': 'LOG_g.jsonl', 'source_state_sha': sha(root/'STATE_g.json')}
        state, proof = preflight(root, protocol)
        (root/'preflight.json').write_text(json.dumps(proof, indent=2)+'\n')
        (root/'reconciled_baseline.json').write_text(json.dumps(state)+'\n')
        print(json.dumps({k: v for k, v in proof.items() if k != 'events'}), flush=True)
        if args.live:
            from observer import start_for_pilot
            if args.resume:
                if state['st'].get('f_budget_id') != budget['id'] or proof['pnl'] <= budget['cutoff']:
                    raise CheckFailed('Butce kimligi veya kalan zarar hakki gecersiz')
                from observer import archive_finished
                archive_finished(root, round(time.time()*1000))
            start_for_pilot(root)
            if args.resume:
                resume_files(root, state, proof, budget, round(time.time()*1000))
            else:
                activate_files(root, state, proof, round(time.time()*1000))
            os.execv(sys.executable, [sys.executable, '-u', str(root/'g.py'), '--live'])
        print('G PARKTA: kontrol gecti; emir gonderilmedi, yeni butce acilmadi.')


def resume_files(root, state, proof, budget, now):
    """Operator-only continuation; original RUN and BUDGET bytes stay unchanged."""
    if (not 0 <= now-proof['checked_ms'] <= 30000
            or state['st'].get('f_budget_id') != budget['id']
            or not all(math.isfinite(state['st'][k]) and state['st'][k] > budget['cutoff']
                       for k in ('pnl', 'pnl_yerel'))):
        raise CheckFailed('Devam kontrolu eski veya butce tukendi')
    from f_budget import read_budget
    if read_budget(root/'BUDGET_G.json', allow_unlimited=True) != budget:
        raise CheckFailed('Devam butcesi degismis')
    from g_guard import verify as verify_active
    verify_active(root, budget)
    stamp = str(now)
    with (root/('RESUME_'+stamp+'.json')).open('x') as f:
        json.dump(dict(proof=proof, budget_id=budget['id']), f)
    with (root/('STATE_g.before_resume_'+stamp+'.json')).open('xb') as f:
        f.write((root/'STATE_g.json').read_bytes())
    state = {**state, 'st': {**state['st'], 'durdu': None}}
    temporary = root/'STATE_g.resume_tmp'
    temporary.write_text(json.dumps(state))
    temporary.replace(root/'STATE_g.json')
    if (root/'STOP_G').exists():
        (root/'STOP_G').rename(root/('STOP_G.before_resume_'+stamp))


if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        # SDK istisnasinin ham metnini veya HTTP basliklarini aciga cikarma.
        print(json.dumps({'status': 'PREFLIGHT_FAILED', 'type': type(ex).__name__,
                          'check': str(ex) if isinstance(ex, CheckFailed) else None}))
        raise SystemExit(1)
