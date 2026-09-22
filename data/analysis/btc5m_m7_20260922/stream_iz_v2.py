"""M7: read-only account/public streams, one host clock, allowlisted records."""
import argparse
from collections import Counter
import contextlib
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import queue
import re
import signal
import threading
import time
import uuid

from emir_iz import kimlik, saat

WS = 'wss://ws-subscriptions-clob.polymarket.com/ws/'
PING_SECONDS = 10


def number(value):
    value = str(value)
    if not re.fullmatch(r'(?:[0-9]{1,80}(?:\.[0-9]{1,18})?|\.[0-9]{1,18})', value):
        raise ValueError('numeric field')
    return value


def identity(value):
    if kimlik(value) is None:
        raise ValueError('identity field')
    return value


def trade_id(value):
    return str(uuid.UUID(value))


def choice(value, allowed):
    if value not in allowed.split():
        raise ValueError('enum field')
    return value


def clean(message, channel):
    """No free text, owner/API identifiers, signatures, auth or exception text."""
    kind = message['event_type']
    choice(kind, 'book price_change last_trade_price tick_size_change' if channel=='market' else 'order trade')
    result = dict(event_type=kind, market=identity(message['market']), timestamp=number(message['timestamp']))
    if kind!='price_change':
        result['asset_id'] = identity(message['asset_id'])
    for key in ('price','size','fee_rate_bps','original_size','size_matched','created_at',
                'expiration','match_time','last_update','old_tick_size','new_tick_size'):
        if message.get(key) is not None:
            result[key] = number(message[key])
    for key, allowed in [('side','BUY SELL'),('type','PLACEMENT UPDATE CANCELLATION TRADE'),
        ('status','LIVE MATCHED CANCELED CANCELLED DELAYED UNMATCHED MATCHED_NOT_BROADCASTED MINED CONFIRMED RETRYING FAILED'),
        ('trader_side','MAKER TAKER'),('order_type','GTC GTD FOK FAK IOC')]:
        if message.get(key) is not None:
            result[key] = choice(message[key],allowed)
    if kind=='order':
        result.update(id=identity(message['id']),type=choice(message['type'],'PLACEMENT UPDATE CANCELLATION'),
                      associate_trades=[trade_id(t) for t in (message.get('associate_trades') or [])])
        for key in ('price','original_size','size_matched','side'):
            if key not in result:
                raise ValueError('incomplete order')
    if kind=='trade':
        result.update(id=trade_id(message['id']),taker_order_id=identity(message['taker_order_id']))
        result['maker_orders'] = [dict(order_id=identity(m['order_id']),
            matched_amount=number(m['matched_amount']),price=number(m['price']),
            **({k:identity(m[k]) for k in ('asset_id',) if m.get(k) is not None}),
            **({k:choice(m[k],'BUY SELL') for k in ('side',) if m.get(k) is not None}))
            for m in message.get('maker_orders',[])]
        for key in ('price','size','side','status'):
            if key not in result:
                raise ValueError('incomplete trade')
    if message.get('transaction_hash') is not None:
        result['transaction_hash'] = identity(message['transaction_hash'])
    if kind=='book':
        for key in ('bids','asks'):
            result[key] = [dict(price=number(x['price']),size=number(x['size'])) for x in message[key]]
    if kind=='price_change':
        result['price_changes'] = [dict(asset_id=identity(c['asset_id']),side=choice(c['side'],'BUY SELL'),
            price=number(c['price']),size=number(c['size']),
            **{k:number(c[k]) for k in ('best_bid','best_ask') if c.get(k) not in (None,'')})
            for c in message['price_changes']]
    return result


def credentials(path):
    """Existing SDK derivation is GET; no key creation, order submission or cancel."""
    from py_clob_client_v2.client import ClobClient
    env = {}
    for line in path.read_text().splitlines():
        if re.match(r'^\s*[A-Za-z_][A-Za-z_0-9]*=',line):
            key,value = line.split('=',1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    logging.disable(logging.CRITICAL)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        client = ClobClient('https://clob.polymarket.com',chain_id=137,key=env['PM_PRIVATE_KEY'],
                            signature_type=2,funder=env['PM_FUNDER'])
        creds = client.derive_api_key()
        client.set_api_creds(creds)
        orders = client.get_open_orders()
    if not isinstance(orders,list):
        raise ValueError('account read failed')
    return dict(apiKey=creds.api_key,secret=creds.api_secret,passphrase=creds.api_passphrase),len(orders)


def roster(seconds):
    import requests
    now = int(time.time())
    markets = []
    with requests.Session() as http:
        for start in range(now//300*300-300,(now+seconds)//300*300+301,300):
            slug = f'btc-updown-5m-{start}'
            response = http.get('https://gamma-api.polymarket.com/markets',params={'slug':slug},timeout=10)
            response.raise_for_status()
            m, = response.json()
            assert m['slug']==slug
            tokens = dict(zip(json.loads(m['outcomes']),json.loads(m['clobTokenIds']),strict=True))
            assert set(tokens)=={'Up','Down'}
            markets.append(dict(S=start,market=identity(m['conditionId']),
                                tokens=[identity(tokens[s]) for s in ('Up','Down')]))
    return markets


def capture(output, markets, auth, seconds, account_count, stop, connector=None, queue_size=4096):
    from websockets.sync.client import connect
    connector = connector or connect
    output.mkdir(parents=True,exist_ok=True)
    session = uuid.uuid4().hex
    path = output/f'{session}.jsonl'
    pending = queue.Queue(maxsize=queue_size)
    stats = {k:Counter() for k in ('market','user')}
    deadline = time.monotonic()+seconds
    known = {m['market'] for m in markets}
    tokens = {m['market']:set(m['tokens']) for m in markets}
    subscriptions = dict(market=dict(type='market',assets_ids=[t for m in markets for t in m['tokens']]),
                         user=dict(type='user',markets=sorted(known),auth=auth))

    def emit(channel,event,received=None,**fields):
        try:
            pending.put_nowait(dict(channel=channel,event=event,received=received or saat(),**fields))
        except queue.Full:
            stats[channel]['queue_overflow'] += 1
            stop.set()

    def reader(channel):
        while not stop.is_set() and time.monotonic()<deadline:
            stats[channel]['connections'] += 1
            connection = stats[channel]['connections']
            try:
                with connector(WS+channel,open_timeout=8,close_timeout=2,max_queue=4096,
                               max_size=2**20,ping_interval=None) as ws:
                    ws.send(json.dumps(subscriptions[channel]))  # Never recorded.
                    emit(channel,'subscription_sent',connection=connection)
                    ping = time.monotonic()-PING_SECONDS
                    pong = time.monotonic()
                    while not stop.is_set() and time.monotonic()<deadline:
                        if time.monotonic()-ping>=PING_SECONDS:
                            ws.send('PING')
                            ping = time.monotonic()
                            stats[channel]['ping'] += 1
                        if time.monotonic()-pong>3*PING_SECONDS:
                            raise TimeoutError('heartbeat')
                        try:
                            raw = ws.recv(timeout=min(.5,max(.001,deadline-time.monotonic())))
                        except TimeoutError:
                            continue
                        received = saat()  # Before JSON parsing and disk/queue work.
                        if raw=='PONG':
                            pong = time.monotonic()
                            stats[channel]['pong'] += 1
                            emit(channel,'pong',received,connection=connection)
                            continue
                        stats[channel]['frames'] += 1
                        try:
                            payload = json.loads(raw)
                            messages = payload if isinstance(payload,list) else [payload]
                        except (ValueError,TypeError):
                            messages = [None]
                        for index,message in enumerate(messages):
                            try:
                                safe = clean(message,channel)
                                if safe['market'] not in known:
                                    raise ValueError('market outside roster')
                                assets = [c['asset_id'] for c in safe['price_changes']] if safe['event_type']=='price_change' else [safe['asset_id']]
                                assets += [m['asset_id'] for m in safe.get('maker_orders',[]) if 'asset_id' in m]
                                if not set(assets)<=tokens[safe['market']]:
                                    raise ValueError('asset outside market')
                            except (ValueError,KeyError,TypeError,AttributeError):
                                stats[channel]['rejected'] += 1
                                emit(channel,'rejected',received,connection=connection,frame=stats[channel]['frames'],index=index)
                                continue
                            stats[channel][safe['event_type']] += 1
                            emit(channel,'data',received,connection=connection,frame=stats[channel]['frames'],index=index,payload=safe)
            except Exception as error:
                stats[channel]['gaps'] += 1
                close = getattr(error,'rcvd',None)
                reason = getattr(close,'reason','').lower()
                emit(channel,'gap',connection=connection,error_type=type(error).__name__,
                     close_code=getattr(close,'code',None),
                     close_reason_class=reason if reason in ('slow consumer','rate limit','unauthorized') else None)
                stop.wait(.5)
            finally:
                emit(channel,'connection_end',connection=connection)

    threads = [threading.Thread(target=reader,args=(ch,),name=f'm7-{ch}') for ch in stats]
    started = saat()
    count,writer_failed = 0,False
    summary = dict(session=session,pid=os.getpid(),started=started,markets=markets,
                   open_orders_at_auth_check=account_count,
                   boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                   source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (Path(__file__),Path(__file__).with_name('emir_iz.py'))})
    try:
        with path.open('x',encoding='utf8') as file:
            file.write(json.dumps(dict(event='session_start',**summary))+'\n')
            for thread in threads:
                thread.start()
            flushed = time.monotonic()
            # ponytail: one buffered writer; overflow invalidates this capture instead of dropping silently.
            while any(t.is_alive() for t in threads) or not pending.empty():
                if (output/'STOP_M7').exists() or time.monotonic()>=deadline:
                    stop.set()
                try:
                    row = pending.get(timeout=.2)
                except queue.Empty:
                    continue
                count += 1
                file.write(json.dumps(dict(session=session,seq=count,written=saat(),**row),separators=(',',':'))+'\n')
                if time.monotonic()-flushed>=1:
                    file.flush()
                    flushed = time.monotonic()
            file.write(json.dumps(dict(event='session_end',session=session,ended=saat(),stats=stats))+'\n')
            file.flush()
            os.fsync(file.fileno())
    except Exception:
        writer_failed = True
        raise
    finally:
        stop.set()
        for thread in threads:
            if thread.ident is not None:
                thread.join(12)
        summary.update(ended=saat(),stats=stats,rows=count,writer_failed=writer_failed,
                       reader_alive=any(t.is_alive() for t in threads),
                       user_events_observed=bool(stats['user']['order']+stats['user']['trade']),
                       full_calibration=False)
        summary['transport_ok'] = (not writer_failed and not summary['reader_alive'] and
            all(c['pong'] and not (c['gaps']+c['rejected']+c['queue_overflow']) for c in stats.values()))
        (output/f'{session}.summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return path,summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credentials',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seconds',type=int,default=360)
    args = parser.parse_args()
    if not 1<=args.seconds<=3600 or (args.out/'STOP_M7').exists():
        raise ValueError('duration or stop marker')
    os.umask(0o077)
    print('M7_STAGE: public_roster',flush=True)
    markets = roster(args.seconds)
    print('M7_STAGE: account_get',flush=True)
    auth,count = credentials(args.credentials)
    stop = threading.Event()
    for sig in (signal.SIGINT,signal.SIGTERM):
        signal.signal(sig,lambda *_:stop.set())
    print('M7_STAGE: capture',flush=True)
    path,summary = capture(args.out,markets,auth,args.seconds,count,stop)
    print(json.dumps(dict(path=str(path),stats=summary['stats'],user_events_observed=summary['user_events_observed'])))
    if not summary['transport_ok']:
        raise RuntimeError('incomplete capture')


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print('M7_FAILED: '+type(error).__name__)
        raise SystemExit(1) from None
