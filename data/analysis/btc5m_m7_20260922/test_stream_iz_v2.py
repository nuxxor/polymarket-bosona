"""Run the actual dual reader with fake wire events; no financial methods exist."""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch

import stream_iz as s

CIDS = ['0x'+'a'*64,'0x'+'b'*64]
OID,TX = '0x'+'c'*64,'0x'+'d'*64
TID = 'f0010000-0000-4000-8000-000000000001'
SECRET = 'not-to-be-logged-api-secret'
MARKETS = [dict(S=300+i*300,market=cid,tokens=[str(10+i*2),str(11+i*2)]) for i,cid in enumerate(CIDS)]
ORDER = dict(event_type='order',id=OID,market=CIDS[0],asset_id='10',side='BUY',price='.50',
    original_size='5',size_matched='0',type='PLACEMENT',status='LIVE',timestamp='1000',
    owner=SECRET,order_owner=SECRET,auth=dict(secret=SECRET),signature=SECRET)
TRADE = dict(event_type='trade',id=TID,taker_order_id='0x'+'e'*64,market=CIDS[0],asset_id='11',
    side='BUY',size='1.340000',price='.50',status='MATCHED',timestamp='1200',match_time='1',
    owner=SECRET,trade_owner=SECRET,transaction_hash=TX,maker_orders=[dict(order_id=OID,
    matched_amount='1.340000',price='.50',asset_id='10',side='BUY',owner=SECRET)])


class Wire:
    def __init__(self,frames):
        self.frames = iter(frames)
        self.sent = []
        self.last_received_ns = []
    def __enter__(self):
        return self
    def __exit__(self,*args):
        pass
    def send(self,message):
        self.sent.append(message)
    def recv(self,timeout):
        time.sleep(.002)
        frame = next(self.frames,None)
        if isinstance(frame,Exception):
            raise frame
        if frame is None:
            time.sleep(.01)
            frame = 'PONG'
        self.last_received_ns.append(time.monotonic_ns())
        return frame


def run_case(root,frames,seconds=.18,queue_size=4096):
    connections = {k:[] for k in frames}
    def connect(url,**kwargs):
        channel = url.rsplit('/',1)[1]
        batches = frames[channel]
        wire = Wire(batches[min(len(connections[channel]),len(batches)-1)])
        connections[channel].append(wire)
        return wire
    with patch.object(s,'PING_SECONDS',.05):
        path,summary = s.capture(root,MARKETS,dict(apiKey=SECRET,secret=SECRET,passphrase=SECRET),
                                seconds,0,threading.Event(),connect,queue_size)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert SECRET not in path.read_text()+json.dumps(summary)
    assert not summary['reader_alive'] and not summary['writer_failed']
    seqs = [r['seq'] for r in rows if 'seq' in r]
    assert seqs==list(range(1,len(seqs)+1))
    assert all(r['written']['mono_ns']>=r['received']['mono_ns'] for r in rows if 'seq' in r)
    for channel,wires in connections.items():
        for wire in wires:
            sub = json.loads(wire.sent[0])
            assert sub['type']==channel
            assert (channel=='user')==('auth' in sub)
            assert all(m=='PING' for m in wire.sent[1:])
    return rows,summary,connections


def main():
    assert SECRET not in json.dumps(s.clean(ORDER,'user'))
    assert SECRET not in json.dumps(s.clean(TRADE,'user'))
    for key in ('price','timestamp'):
        bad = dict(ORDER,**{key:SECRET})
        try:
            s.clean(bad,'user')
        except ValueError:
            pass
        else:
            raise AssertionError('Free text entered numeric field')
    books = [dict(event_type='book',market=m['market'],asset_id=t,timestamp='900',
                  bids=[dict(price='.5',size='20')],asks=[dict(price='.6',size='30')])
             for m in MARKETS for t in m['tokens']]
    changes = dict(event_type='price_change',market=CIDS[0],timestamp='1100',price_changes=[
        dict(asset_id='10',side='BUY',price='.5',size='25',best_bid='.5',best_ask='.6'),
        dict(asset_id='11',side='SELL',price='.5',size='25',best_bid='.4',best_ask='.5')])
    update = dict(ORDER,type='UPDATE',size_matched='1.34',associate_trades=[TID],timestamp='1200')
    late = dict(update,size_matched='0',timestamp='1100')
    cancel = dict(ORDER,type='CANCELLATION',status='CANCELED',timestamp='1400')
    confirm = dict(TRADE,status='CONFIRMED',timestamp='1500')
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        rows,summary,_ = run_case(root/'normal',dict(
            market=[['PONG',json.dumps(books),json.dumps(changes)]],
            user=[['PONG',json.dumps([ORDER,update,TRADE,TRADE,late,cancel,confirm])]]))
        user = [r['payload'] for r in rows if r.get('event')=='data' and r['channel']=='user']
        assert len(user)==7 and user[2]==user[3]  # Repeated updates retained, not extra economic fills.
        assert user[1]['size_matched']=='1.34' and user[4]['timestamp']=='1100'
        assert Counter(r['type'] for r in user if r['event_type']=='order')=={'PLACEMENT':1,'UPDATE':2,'CANCELLATION':1}
        assert {r['payload']['market'] for r in rows if r.get('event')=='data' and r['channel']=='market'}==set(CIDS)
        assert summary['user_events_observed'] and not summary['full_calibration']
        assert summary['transport_ok']
        assert sum(c['gaps']+c['rejected']+c['queue_overflow'] for c in summary['stats'].values())==0
        bad = deepcopy(ORDER)
        bad['asset_id']='99'
        failure = RuntimeError(SECRET)
        failure.rcvd = SimpleNamespace(code=1013,reason='slow consumer')
        rows,summary,_ = run_case(root/'gap',dict(market=[['PONG',json.dumps(books)]],
            user=[['PONG',json.dumps(bad),failure],['PONG',json.dumps(update)]]),seconds=.7)
        assert summary['stats']['user']['gaps']==1 and summary['stats']['user']['connections']==2
        assert summary['stats']['user']['rejected']==1
        assert not summary['transport_ok']
        assert any(r.get('event')=='gap' and r['error_type']=='RuntimeError' for r in rows)
        assert any(r.get('event')=='gap' and r['close_code']==1013 and r['close_reason_class']=='slow consumer' for r in rows)
        rows,summary,_ = run_case(root/'overflow',dict(market=[['PONG',json.dumps(books*100)]],user=[['PONG']]),queue_size=1)
        assert sum(c['queue_overflow'] for c in summary['stats'].values())>0
        assert not summary['transport_ok']
    print('M7: real dual loop, redaction, partial/repeated/late events, two markets, reconnect and overflow passed')


if __name__=='__main__':
    main()
