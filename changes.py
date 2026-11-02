import re, json
from datetime import datetime
L=open('wt_2026.txt',encoding='utf8').read().splitlines()
i=[k for k,l in enumerate(L) if 'id="changes"' in l][0]
rows=[];cur=[]
for l in L[i+1:]:
    l=l.strip()
    if l.startswith('|}'): break
    if l.startswith('|-'):
        if cur: rows.append(cur); cur=[]
        continue
    if l.startswith('!'): continue
    if l.startswith('|'):
        for c in l[1:].split('||'): cur.append(c.strip())
if cur: rows.append(cur)
clean=lambda c: re.sub(r'<ref[^>]*/>|<ref.*?</ref>|<ref.*','',c).strip()
out=[]
for r in rows:
    r=[clean(c) for c in r]
    try: dt=datetime.strptime(re.sub(r'\s+',' ',r[0]),'%B %d, %Y').date()
    except Exception: continue
    add=r[1] if len(r)>1 else ''; rem=r[3] if len(r)>3 else ''
    nm=re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', lambda m: m.group(1), r[2]).strip() if len(r)>2 else ''
    out.append(dict(date=str(dt),added=add,added_name=nm,removed=rem,reason=(r[5] if len(r)>5 else '')[:120]))
json.dump(out,open('changes.json','w'),indent=0)
years=sorted({o['date'][:4] for o in out}); print(len(out),years[0],years[-1])
for y in ['2010','2013','2020','2024']:
    print(y,[(o['date'][5:],o['added'],o['removed']) for o in out if o['date'][:4]==y][:40])
