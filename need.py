import json, pandas as pd
c={int(k):v for k,v in json.load(open('constituents.json')).items()}
d=pd.read_pickle('px.pkl')
# tickers whose Yahoo symbol now belongs to a different company (before the given year-end, data is not this company)
BAD={'BBBY','FB','PCLN','SHLD','GOLD','LIFE','MICC','SPLS','SNDK','EA','WBD','DELL','FOX','FOXA','NWSA'}
RENAME={'CTRP':'TCOM','HANS':'MNST','RIMM':'BB','WLTW':'WTW','SYMC':'GEN','CMCSK':'CMCSA','FB':'META','PCLN':'BKNG','LMCA':'FWONA','LMCK':'FWONK','ERTS':None}
def ye(s,y):
    s=s[s.index<=f'{y}-12-31'].dropna()
    return s.iloc[-1] if len(s) and s.index[-1].year==y and s.index[-1].month==12 and s.index[-1].day>=24 else None
def yret(t,y):
    t2=RENAME.get(t,t)
    if t2 is None or t2 not in d: return None
    if t in BAD and t not in RENAME: return None
    a,b=ye(d[t2],y-1),ye(d[t2],y)
    return None if a is None or b is None else b/a-1
need={}
for Y in range(2010,2026):
    for t in c[Y]:
        t=t.replace('.','-')
        r=yret(t,Y)
        if r is None: need.setdefault(t,[]).append(Y)
json.dump(need,open('need.json','w'))
for t,v in sorted(need.items()): print(t,v)
print(len(need))
