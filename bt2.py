import json, pandas as pd, os, csv
c={int(k):[t.replace('.','-') for t in v] for k,v in json.load(open('constituents.json')).items()}
names={int(k):v for k,v in json.load(open('names.json')).items()}
d=pd.read_pickle('px.pkl')
need=json.load(open('need.json'))
mt=json.load(open('mt.json')) if os.path.exists('mt.json') else {}
man=json.load(open('manual.json')) if os.path.exists('manual.json') else {}
s1=json.load(open('s1_data.json'))   # {ticker:{year:{"r":..,"src":..}}}
DELIST=json.load(open('delist.json'))          # ticker -> year it stopped trading (partial final year)
def gone(t,Y): return DELIST.get(t) is not None and DELIST[t]<=Y and not (t in BAD and BAD[t]<9999 and Y>=BAD[t])
# Yahoo symbols reused by another company: first year whose return Yahoo prices correctly (9999 = never)
BAD={'BBBY':9999,'FB':9999,'PCLN':9999,'SHLD':9999,'GOLD':9999,'LIFE':9999,'MICC':9999,'SPLS':9999,'SNDK':9999,'EA':9999,'WBD':9999,'DELL':2017,'FOX':2020,'FOXA':2020,'NWSA':2014}
RENAME={'MYL':'VTRS','CTRP':'TCOM','HANS':'MNST','RIMM':'BB','WLTW':'WTW','SYMC':'GEN','CMCSK':'CMCSA','FB':'META','PCLN':'BKNG','LMCA':'FWONA','LMCK':'FWONK'}
CLASS={'GOOGL':'GOOG','FOX':'FOXA','DISCK':'DISCA','LMCK':'LMCA','LBTYK':'LBTYA','LBTYB':'LBTYA','NWS':'NWSA','LILAK':'LILA','FWONK':'FWONA','CMCSK':'CMCSA'}
LAST=d.index[-1]
def ye(s,y):
    s=s[s.index<=f'{y}-12-31'].dropna()
    if not len(s): return None
    i=s.index[-1]
    return s.iloc[-1] if (i.year==y and i.month==12 and i.day>=24) or (y==LAST.year and i==LAST) else None
def yret(t,y):
    """-> (return, source) or (None, None)"""
    if str(y) in man.get(t,{}): m=man[t][str(y)]; return m['r'],m['src']
    t2=RENAME.get(t,t)
    if t2 in d and not (t in BAD and t not in RENAME and y<BAD[t]):
        a,b=ye(d[t2],y-1),ye(d[t2],y)
        if a is not None and b is not None: return float(b/a-1),'yahoo'
    r1=s1.get(t,{}).get('rows',{})
    if str(y) in r1: return r1[str(y)]['chg'],'1stock1'
    rows=mt.get(t,{}).get('rows',{})
    if str(y) in rows and (mt[t]['ts'][:4]>str(y) or DELIST.get(t)==y): return rows[str(y)]['chg'],'archive'
    return None,None
rows=[];picks=[];gaps=[]
for Y in range(2010,2026):
    best={}
    for t in c[Y]:
        r,src=yret(t,Y)
        if r is None: gaps.append((Y,t)); continue
        k=CLASS.get(t,t)
        if k not in best or r>best[k][0]: best[k]=(r,t)
    rk=[x for x in sorted(best.values(),reverse=True) if not gone(x[1],Y)][:10]
    H=Y+1; vals=[]
    for i,(r,t) in enumerate(rk):
        h,src=yret(t,H)
        note=''
        if DELIST.get(t)==H: note='持有年内被收购，按收购对价计，之后视为现金' if src in ('1stock1','deal') else '持有年内被收购退市，按最后成交价计，之后视为现金'
        picks.append(dict(hold_year=H,sel_year=Y,rank=i+1,ticker=t,company=names[Y].get(t,t),sel_return=round(r,4),hold_return=None if h is None else round(h,4),end_value=None if h is None else round(1+h,4),source=src or 'missing',note=note))
        vals.append(h)
    q,_=yret('QQQ',H)
    ok=[v for v in vals if v is not None]
    rows.append(dict(hold_year=H,sel_year=Y,strategy_return=round(sum(ok)/len(ok),4),qqq_return=round(q,4),end_value=round(sum(1+v for v in ok),3),picks_priced=len(ok),universe=len(c[Y]),universe_priced=len(c[Y])-sum(1 for g in gaps if g[0]==Y),tenth_cutoff=round(rk[-1][0],4),partial=H==LAST.year,as_of=str(LAST.date()) if H==LAST.year else f'{H}-12-31'))
if __name__=='__main__':
    for r in rows: print(r['hold_year'],'%6.1f%% vs QQQ %6.1f%%'%(r['strategy_return']*100,r['qqq_return']*100),'priced %d/%d'%(r['universe_priced'],r['universe']),'| ',' '.join(p['ticker'] for p in picks if p['hold_year']==r['hold_year']))
    print('gaps:',len(gaps)); 
    for w,data in (('yearly.csv',rows),('picks.csv',picks)):
        with open(w,'w',newline='',encoding='utf8') as f:
            wr=csv.DictWriter(f,fieldnames=list(data[0])); wr.writeheader(); wr.writerows(data)
    json.dump(gaps,open('gaps.json','w'))
