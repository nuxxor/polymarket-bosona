#!/usr/bin/env python3
"""Chainlink Data Streams REST istemcisi. Kimlik = STREAMS_USERNAME + STREAMS_API_SECRET.
Cloudflare tarayici UA istiyor. Sir DEGERI asla basilmaz."""
import os, hmac, hashlib, time, json, urllib.request, urllib.error
HOST = 'api.dataengine.chain.link'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'

def _creds():
    d = {}
    for line in open(os.path.expanduser('~/.config/chainlink_streams/creds.env')):
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=', 1)
            d[k.replace('export ', '').strip()] = v.strip().strip('"').strip("'")
    return d['STREAMS_USERNAME'], d['STREAMS_API_SECRET']

def call(path, retries=3):
    cid, secret = _creds()
    for a in range(retries):
        ts = str(int(time.time() * 1000))
        bh = hashlib.sha256(b'').hexdigest()
        sig = hmac.new(secret.encode(), f"GET {path} {bh} {cid} {ts}".encode(), hashlib.sha256).hexdigest()
        req = urllib.request.Request('https://' + HOST + path, headers={'Authorization': cid,
            'X-Authorization-Timestamp': ts, 'X-Authorization-Signature-SHA256': sig,
            'User-Agent': UA, 'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read()[:200]
            if e.code in (429, 500, 502, 503) and a < retries - 1:
                time.sleep(1.5 * (a + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {body}")
        except Exception:
            if a < retries - 1:
                time.sleep(1.5 * (a + 1)); continue
            raise
