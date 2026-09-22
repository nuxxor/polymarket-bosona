#!/usr/bin/env python3
"""Two frozen explanatory scores using public context and OWN inventory; no actions."""
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import candidate as c  # noqa: E402
import research as r  # noqa: E402


def score(name,age,prices,context,inventory):
    if name not in ('H1_continuous_value','H2_inventory_cost'):
        raise ValueError('only the two preregistered explanatory hypotheses')
    q=inventory['q']
    net=q[0]-q[1]
    if abs(net)<1e-8 or not 600<=age<900:
        return None
    side=0 if net>0 else 1
    price=prices[side]
    prob=context['final_up_prob'] if side==0 else 1-context['final_up_prob']
    basis=sum(n*p for n,p in inventory['lots'][side])/abs(net)
    x=dict(price=price,age=age,risk_log=math.log1p(max(0,inventory['cash']-min(q))),
        edge=prob-c.unit_cost(price,.07),momentum=(1 if side==0 else -1)*context['momentum10'],
        discount=basis-price,net_log=math.log1p(abs(net)),imbalance=abs(net)/sum(q))
    fit=r.read(Path(__file__).resolve().parent/'results/hypothesis_models.json')['fitted'][name]
    if not all(math.isfinite(x[k]) for k in fit['features']):
        raise ValueError('nonfinite causal features')
    z=fit['intercept']+sum(b*(x[k]-m)/sd for k,m,sd,b in zip(fit['features'],fit['mean'],fit['scale'],fit['coefficients']))
    return 1/(1+math.exp(-max(-700,min(700,z))))
