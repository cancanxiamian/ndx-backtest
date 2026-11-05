import json
from bt2 import c, names, yret, CLASS, DELIST, LAST, gone
ch=json.load(open('changes.json'))
adds={}
for o in ch:
    if o['added']: adds.setdefault(int(o['date'][:4]),[]).append(o['added'].replace('.','-'))
rank={}
for Y in range(2010,2026):
    uni=set(c[Y])|set(adds.get(Y,[]))
    best={}
    for t in uni:
        r,_=yret(t,Y)
        if r is None or gone(t,Y): continue
        k=CLASS.get(t,t)
        if k not in best or r>best[k][0]: best[k]=(r,t)
    rank[Y]=[t for _,t in sorted(best.values(),reverse=True)]
qs={Y+1:yret('QQQ',Y+1)[0] for Y in range(2010,2026)}
def run(N,show=False):
    g=1; yrs=[]
    for Y in range(2010,2025):
        picks=rank[Y][:N]; h=[yret(t,Y+1)[0] for t in picks]
        if None in h: print('  missing hold',Y+1,[t for t,x in zip(picks,h) if x is None])
        h=[x for x in h if x is not None]
        r=sum(h)/len(h); g*=1+r; yrs.append((Y+1,r,picks,h))
    wins=sum(r>qs[y] for y,r,_,_ in yrs); worst=min(yrs,key=lambda x:x[1])
    if show:
        for y,r,p,h in yrs: print(y,'%+6.1f%%'%(r*100),'QQQ %+6.1f%%'%(qs[y]*100),'  ',', '.join(f'{t} {x*100:+.0f}%' for t,x in zip(p,h)))
    return g,g**(1/15)-1,wins,worst
q=1
for y in range(2011,2026): q*=1+qs[y]
print('QQQ growth %.2f cagr %.1f%%'%(q,(q**(1/15)-1)*100))
for N in range(1,11):
    g,cg,w,wo=run(N); print('top%-2d growth %5.2f  cagr %5.1f%%  wins %2d/15  worst %d %+.1f%%'%(N,g,cg*100,w,wo[0],wo[1]*100))
print('--- top3 by year')
run(3,True)
y26=[yret(t,2026)[0] for t in rank[2025][:3]]; print('2026 YTD top3',rank[2025][:3],'%+.1f%%'%(sum(y26)/3*100))
