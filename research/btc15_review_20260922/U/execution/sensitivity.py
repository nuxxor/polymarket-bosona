#!/usr/bin/env python3
"""Re-run unchanged frozen candidate with corrected historical accessor only; proxy prices, no fills."""
import gzip
import json

import audit as a


def run():
    c = a.c
    universe = [w for w in a.read(a.R/'results/universe.json') if w['group'] == 'btc_15m']
    tokens = {w['slug']: json.loads(a.read(a.R/'raw/markets'/f'{w["slug"]}.json')['clobTokenIds']) for w in universe}
    wanted = {t for ts in tokens.values() for t in ts}
    history = {}
    for path in sorted((a.R/'raw/histories').glob('*.json')):
        for token, values in a.read(path)['response']['history'].items():
            if token in wanted:
                if token in history:
                    assert history[token] == values
                history[token] = values
    indexed = {slug: [([x['t'] for x in history.get(token, [])], history.get(token, [])) for token in ts]
               for slug, ts in tokens.items()}
    with gzip.open(a.HERE/'corrected_contexts.json.gz', 'rt') as stream:
        context = json.load(stream)
    original_context = a.read(a.R/'raw/btc15_context.json')
    comparisons = {}
    for age in (180, 600, 840, 870):
        for period in ('discovery', 'chronological', 'update'):
            model, market, ages = [], [], []
            for w in universe:
                now = w['S']+age
                key = f'{w["S"]}:{now}'
                h = c.study.at(indexed[w['slug']], now-5)
                if c.r.period(w['S']) != period or key not in original_context or not h:
                    continue
                y = int(w['winner'] == 0)
                model.append(dict(S=w['S'], p=original_context[key]['final_up_prob'], y=y))
                market.append(dict(S=w['S'], p=h['p'][0], y=y))
                ages.append(h['ages'][0]+5)
            comparisons[f'{age}:{period}'] = dict(model=a.calibration(model), sampled_up_price=a.calibration(market),
                mean_price_age=sum(ages)/len(ages) if ages else None,
                over99_confident=sum(x['p'] < .01 or x['p'] > .99 for x in model),
                over99_wrong=sum((x['p'] < .01 and x['y'] == 1) or (x['p'] > .99 and x['y'] == 0) for x in model))
    a.save('calibration_market_comparison.json', comparisons)
    out = a.HERE/'historical_sensitivity'
    out.mkdir(exist_ok=True)
    def read(path):
        if path == out/'universe.json':
            return universe
        if path == a.R/'raw/btc15_context.json':
            return context
        return a.read(path)
    def save(path, value):
        assert path.is_relative_to(out), path
        path.write_text(json.dumps(value, separators=(',', ':'))+'\n')
    c.r.OUT, c.r.read, c.r.save = out, read, save
    c.study.history_index = lambda: indexed
    c.replay()
    original = a.read(a.R/'results/candidate_scenario_rows.json')
    updated = a.read(out/'candidate_scenario_rows.json')
    summary = {}
    for arm in ('entry_only', 'completion_only', 'managed'):
        def selected(rows):
            return {x['S']: x for x in rows if x['entry'] == 'discount' and x['slip'] == 0 and x['arm'] == arm and x['entered']}
        old, new = selected(original), selected(updated)
        summary[arm] = dict(original_entries=len(old), corrected_entries=len(new),
                            original_pnl=sum(x['pnl'] for x in old.values()), corrected_pnl=sum(x['pnl'] for x in new.values()),
                            original_adds=sum(x['added'] for x in old.values()), corrected_adds=sum(x['added'] for x in new.values()),
                            lost_entries=sorted(old.keys()-new.keys()), added_entries=sorted(new.keys()-old.keys()),
                            common_changed_paths=[s for s in old.keys() & new.keys() if old[s]['events'] != new[s]['events']])
    a.save('history_policy_sensitivity.json', dict(summary=summary,
           note='Unchanged candidate; context correction changes sigma/probability, not just availability. '
                'All 36 previous combinations retained as sensitivity, no new threshold search. '
                'Historical sampled-price scenario, not executable trading performance.'))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    run()
