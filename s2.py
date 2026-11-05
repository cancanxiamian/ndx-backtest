import json, csv
from bt2 import c, names, yret, CLASS, DELIST, LAST, gone
ch=json.load(open('changes.json'))
adds={}
for o in ch:
    if o['added']: adds.setdefault(int(o['date'][:4]),[]).append((o['added'].replace('.','-'),o['date'],o['added_name']))
rows=[]; gaps=[]
for Y in range(2010,2026):
    uni={t:('年初已在指数中',names[Y].get(t,t)) for t in c[Y]}
    for t,dt,nm in adds.get(Y,[]):
        if t not in uni: uni[t]=(f'{dt} 加入指数',nm)
    best={}
    for t in uni:
        r,src=yret(t,Y)
        if r is None: gaps.append((Y,t)); continue
        if gone(t,Y): continue
        k=CLASS.get(t,t)
        if k not in best or r>best[k][0]: best[k]=(r,t)
    rk=sorted(best.values(),reverse=True)
    r,t=rk[0]; h,src=yret(t,Y+1); q,_=yret('QQQ',Y+1)
    note='持有年内被收购，按收购对价计，之后视为现金' if DELIST.get(t)==Y+1 else ''
    rows.append(dict(hold_year=Y+1,sel_year=Y,ticker=t,company=uni[t][1],membership=uni[t][0],sel_return=round(r,4),hold_return=round(h,4),qqq_return=round(q,4),
        runner_up=' / '.join(f'{x[1]} {x[0]*100:+.0f}%' for x in rk[1:3]),universe=len(uni),universe_priced=len(uni)-sum(1 for g in gaps if g[0]==Y),
        partial=Y+1==LAST.year,as_of=str(LAST.date()) if Y+1==LAST.year else f'{Y+1}-12-31',source=src,note=note))
if __name__=='__main__':
    s=q=1
    for r in rows:
        if not r['partial']: s*=1+r['hold_return']; q*=1+r['qqq_return']
        print(r['hold_year'],r['ticker'],r['company'],'|',r['membership'],'| sel %+.0f%%'%(r['sel_return']*100),'hold %+.1f%%'%(r['hold_return']*100),'QQQ %+.1f%%'%(r['qqq_return']*100),'|',r['runner_up'],r['source'])
    print('growth 15y',round(s,2),'vs QQQ',round(q,2),'| gaps',[g for g in gaps if g not in json.load(open('gaps.json'))])
    with open('top1.csv','w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
