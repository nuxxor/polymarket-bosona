#!/usr/bin/env python3
"""Operator icin E -> F, 120 dakika. Bayraksiz yalniz durum okur."""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

MANIFEST = 'F_RELEASE.json'
RELEASE_FILES = ('ab.py','emir_iz.py','f.py','f_model.py','f_gecis.py','f_budget.py','d_olcum.py','../data/f_research/model.json')


def devir_kontrol(state, kapanis):
    st, pen = state['st'], state['pen']
    if not kapanis or kapanis.get('lane') != 'E' or kapanis.get('sebep') not in ('STOP', 'sure', 'sinyal'):
        raise ValueError('E temiz kapanisi yok veya kesici kilitli')
    if st.get('durdu') == 'kesici':
        raise ValueError('Zarar butcesi kilitli; F sifirlayamaz')
    for key in ('pencere', 'emir', 'pnl'):
        if st[key] != kapanis[key]:
            raise ValueError('E kapanisi ile state farkli')
    if not all(math.isfinite(st[k]) for k in ('pnl', 'pnl_yerel')):
        raise ValueError('Gecersiz PnL')
    if abs(st['pnl'] - st['pnl_yerel']) > .0002:
        raise ValueError('E muhasebesi mutabik degil')
    if min(st['pnl'], st['pnl_yerel']) <= -10:
        raise ValueError('Toplam zarar butcesi tukenmis')
    if any(w.get('kol') not in ('D','E') for w in pen.values()):
        raise ValueError('Beklenmeyen lane gecmisi')
    if any(r.get('durum') not in ('kapali', 'dolu') or r.get('gonderiliyor')
           for w in pen.values() for r in w['emir']):
        raise ValueError('E acik/belirsiz/gonderilen emir var')
    return dict(onceki_pnl=st['pnl'], onceki_pnl_yerel=st['pnl_yerel'],
                onceki_pencere=st['pencere'], bekleyen_onceki=sum(not w.get('cozuldu') for w in pen.values()),
                f_sure_dk=120, toplam_kesici=-10)


def verify_release(bot):
    manifest=json.loads((bot/MANIFEST).read_text())
    if set(manifest['sha256'])!=set(RELEASE_FILES):
        raise ValueError('F dagitim dosya listesi eksik/farkli')
    for name,digest in manifest['sha256'].items():
        if hashlib.sha256((bot/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('F dosyasi degismis: '+name)
    from f_model import load_model
    model,_=load_model(bot/'../data/f_research/model.json')
    if not model.get('ready_live'):
        raise ValueError('F model dogrulamasi tamamlanmamis')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uygula', action='store_true', help='Operator: E durdur, muhasebeyi devret, F baslat')
    args = parser.parse_args()
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        import ab  # --live yok: SDK/kimlik kurulmaz; mevcut yazici tespiti.
    e = Path(__file__).resolve().parent
    d = e.parent.with_name('polymarket-bosona-e') / 'bot'

    def writers():
        found = []
        for proc in Path('/proc').glob('[0-9]*'):
            try:
                argv = (proc / 'cmdline').read_bytes().decode('utf8', 'ignore').split('\0')
                if 'python' in argv[0] and ab.d_baska_yazici(argv, os.readlink(proc / 'cwd')):
                    found.append((int(proc.name), str(d / 'e.py') in argv))
            except (OSError, ProcessLookupError):
                continue
        return found

    if not args.uygula:
        print(json.dumps(dict(yazicilar=writers(), f_parkta=(e / 'STOP_F').exists(),
                              f_state_var=(e / 'STATE_f.json').exists(), sure_dk=120)))
        return
    with (e / '.f_gecis.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_release(e)
        if not (e / 'STOP_F').exists():
            raise SystemExit('F parkta degil')
        if any((e / n).exists() for n in ('STATE_f.json', 'LOG_f.jsonl', 'DEVIR_E_F.json', 'STATE_f.json.devir', 'STOP_F.devir')):
            raise SystemExit('F gecmisi/devir var; tekrar kopyalayip butce sifirlanamaz')
        if any(not is_d for _, is_d in writers()):
            raise SystemExit('E disinda canli yazici var')
        if subprocess.run(['tmux','has-session','-t','bosona-f'],capture_output=True).returncode==0:
            raise SystemExit('bosona-f oturumu zaten var')
        latest=json.loads((e/'../data/d_olcum/latest.json').read_text())
        if not latest.get('connected') or any(not 0<=time.time()*1000-latest['prices'][s][field]<=3000
                for s in ('crypto_prices_chainlink','crypto_prices_twap_sixty') for field in ('received_ms','observed_ms')):
            raise SystemExit('F fiyat kaydedicisi hazir degil')
        (d / 'STOP_E').touch()
        end = time.monotonic() + 180
        while writers():
            if time.monotonic() >= end:
                raise SystemExit('E kapanmadi; zorla kapatma yok, F parkta')
            time.sleep(1)
        raw = (d / 'STATE_e.json').read_bytes()
        state = json.loads(raw)
        kapanis = None
        for line in (d / 'LOG_e.jsonl').open():
            event = json.loads(line)
            if event.get('k') == 'SURUM': kapanis = None
            if event.get('k') == 'bitti': kapanis = event
        proof = devir_kontrol(state, kapanis)
        proof.update(utc_ms=round(time.time()*1000), onceki_state_sha=hashlib.sha256(raw).hexdigest(),
                     f_release=json.loads((e / MANIFEST).read_text()), onceki_kapanis=kapanis)
        with (e / 'DEVIR_E_F.json').open('x') as f:
            json.dump(proof, f, indent=2)
        with (e / 'STATE_f.json.devir').open('xb') as f:
            f.write(raw)
        os.replace(e / 'STATE_f.json.devir', e / 'STATE_f.json')
        (e / 'STOP_F').rename(e / 'STOP_F.devir')
        try:
            subprocess.run(['tmux', 'new-session', '-d', '-s', 'bosona-f', sys.executable,
                            '-u', str(e / 'f.py'), '--live', '--dk', '120'], check=True)
        except subprocess.CalledProcessError:
            (e / 'STOP_F').touch()
            raise
        print('F baslatma istendi: 120 dakika; LIVE basladi kaydi ayrica teyit edilmeli.')
        print('Izleme: tmux attach -t bosona-f')


if __name__ == '__main__':
    main()
