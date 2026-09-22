#!/usr/bin/env python3
"""Build results/audit_verification.json (+ .md) from the workflow return saved as results/audit_workflow_return.json.

Structure expected: {audited:[{dimension,summary,findings:[{id,title,claim,severity,verdict,root_cause_class,
verification:{votes:[{refuted,confidence,reason}],refuted_count,survives}}]}], survivors, killed, critic, gapResults}."""
import json
from pathlib import Path

MY = Path(__file__).resolve().parents[1]


def rows_of(res, tag):
    out = []
    for r in res:
        for f in r.get('findings', []):
            v = f.get('verification', {})
            out.append(dict(stage=tag, dimension=r.get('dimension'), id=f.get('id'), title=f.get('title'), severity=f.get('severity'),
                            verdict=f.get('verdict'), root_cause=f.get('root_cause_class'), refuted=v.get('refuted_count'),
                            votes=len(v.get('votes', [])), survives=v.get('survives'),
                            refuter_reasons=[x.get('reason', '')[:220] for x in v.get('votes', []) if x.get('refuted')]))
    return out


def main():
    w = json.load(open(MY/'results/audit_workflow_return.json'))
    rows = rows_of(w.get('audited', []), 'audit')+rows_of(w.get('gapResults', []), 'gap')
    summary = dict(findings=len(rows), survived=sum(1 for x in rows if x['survives']), killed=sum(1 for x in rows if x['survives'] is False),
                   by_severity={s: dict(n=sum(1 for x in rows if x['severity'] == s), survived=sum(1 for x in rows if x['severity'] == s and x['survives']))
                                for s in ('decision_changing', 'important', 'minor')},
                   critic_gaps=[g['key'] for g in (w.get('critic') or {}).get('gaps', [])])
    json.dump(dict(summary=summary, rows=rows), open(MY/'results/audit_verification.json', 'w'), indent=1, ensure_ascii=False)
    lines = ['| aşama | boyut | id | başlık | önem | ajan hükmü | çürüten/oy | sonuç |', '|---|---|---|---|---|---|---:|---|']
    for x in rows:
        lines.append(f"| {x['stage']} | {x['dimension']} | {x['id']} | {x['title'][:80]} | {x['severity']} | {x['verdict']} | {x['refuted']}/{x['votes']} | {'hayatta' if x['survives'] else 'çürütüldü'} |")
    (MY/'results/audit_verification.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
