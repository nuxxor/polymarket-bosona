"""Regenerate the compact comparison and public-clock parent paths from a saved cut."""
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from decimal import Decimal as D
from pathlib import Path
import json

import study as s

ROOT=Path(__file__).resolve().parent


def main():
    report=s.read(ROOT/'latest.json')
    cut=ROOT/'cuts'/Path(report['cut']).name
    paths={}
    lines=['# G1 / Bosona: aynı piyasa ilk okuma', '',
           'Kesit: '+datetime.fromtimestamp(report['as_of_ms']/1000,timezone.utc).isoformat(), '',
           'Kamu nakit maliyeti ve sonuç ödemesi; rebate/sabit gider hariç. Açık sonuç null. '
           'Saatler TR. İlk pilot, süresiz ilk koşu ve yeniden devam ayrı dönemlerdir.', '',
           '| Pencere TR | G sonucu $ | Bosona sonucu $ | İlk dolum yaşı G/Bosona | G yerel pay teyidi |',
           '|---|---:|---:|---|---|']
    for item in report['rows']:
        start=item['S'];actors=item['actors']
        clock=datetime.fromtimestamp(start,timezone(timedelta(hours=3))).strftime('%H:%M')
        g,b=actors.get('G',{}),actors.get('Bosona',{})
        lines.append(f"| {clock} | {g.get('pnl')} | {b.get('pnl')} | {g.get('first_fill_age')}/{b.get('first_fill_age')} | {g.get('quantities_match_local')} |")
        for actor,value in actors.items():
            if value.get('status')=='missing':continue
            rows=s.read(cut/f'{start}_{actor}.json')['rows']
            tokens=json.loads(s.read(cut/f'{start}_market.json')['clobTokenIds'])
            groups=defaultdict(list)
            for row in rows:
                if row['type']=='TRADE':groups[row['timestamp']].append(row)
            fills=value['execution']['rows'];first={}
            for fill in fills:
                first[fill['order_hash']]=min(first.get(fill['order_hash'],float('inf')),min(fill['public_seconds']))
            net=D(0);steps=[]
            for timestamp,group in sorted(groups.items()):
                before=net
                for row in group:
                    net+=D(str(row['size']))*(1 if s.side(row,tokens)==0 else -1)*(1 if row['side']=='BUY' else -1)
                matching=[f for f in fills if timestamp in f['public_seconds']]
                parents={f['order_hash'] for f in matching}
                steps.append(dict(age=timestamp-start,net_before=before,net_after=net,
                    same_second_order_unknown=len({r['asset'] for r in group})>1,
                    trades=[{k:r[k] for k in ('side','outcomeIndex','size','price','usdcSize','transactionHash')} for r in group],
                    first_seen_filled_parents=sorted(p for p in parents if first[p]==timestamp),
                    continuing_filled_parents=sorted(p for p in parents if first[p]<timestamp),
                    roles=sorted({f['role'] for f in matching})))
            paths[f'{start}_{actor}']=steps
    lines+=['', '## Muhasebe ve yorum sınırları', '',
        '- Her snapshot tek başına tam condition geçmişi sorgular; aynı görünen gerçek satırlar korunur. Sayfalar arası belirsiz tekrar kabul edilmez.',
        '- Nakit ve sonuç hesabı bağımsız trade hesabıyla eşleşir. BUY/SELL miktarları ve nakitleri V2 receipt/log ile doğrulanır; gerçek maker/taker ve parent yalnız bu kapsamda bilinir.',
        '- Boş asset taşıyan REDEEM, geçerli outcomeIndex ile ödeme tarafına bağlanır ve işaretlenir. Kaybeden tokenların zincirde yakılması ve harici transferler ayrıca doğrulanmış değildir; tam zincir bakiyesi denetimi iddiası yok.',
        '- Public API saniyesi emir verme anı değildir. Parent ilk dolum zamanı da ilk emir verme zamanı değildir. Aynı saniyede iki taraf varsa sıra belirsizdir.',
        '- İşlemsiz gözlenen piyasa, hiç emir verilmediğini kanıtlamaz. G tarafından atlanan pencere ileri takvimden çıkarılmaz.',
        '- Yerel state, Gamma ve iki activity yanıtı farklı zamanlarda alınır. Açık pencerede miktar farkı veya Gamma sonucundan önce görülen redeem, tek başına bot muhasebe hatası sayılmaz; sonraki kesitte yeniden kontrol edilir.',
        '- trade_only_floor, gözlenen bütün işlemlerin iki olası sonuçtaki düşük ödemesidir. Kapanışın yarattığı alfa veya alternatif strateji PnL’si değildir.',
        '- İleri evren: 14:05–16:05 TR, 24 slot; araştırma süreç çıkışı 16:20 TR. Worker ilk veri kesitini daha sonra toplar; protokol önceden dondurulmuştur. Bu işlem gönderen shadow değildir.',
        '', '## Tekrar çalıştırma', '', '```bash',
        'python3 '+str(ROOT/'check.py'), 'python3 '+str(ROOT/'report.py'), '```', '']
    s.save(ROOT/'paths.json',paths)
    (ROOT/'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps(dict(actor_paths=len(paths),report=str(ROOT/'REPORT.md'))))


if __name__=='__main__':main()
