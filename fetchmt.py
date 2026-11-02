import requests, json, re, time, os, sys
S=requests.Session(); S.headers['User-Agent']='ndx-backtest/1.0 (personal research)'
def latest(url):
    for i in range(4):
        try:
            r=S.get('https://archive.org/wayback/available',params=dict(url=url,timestamp='20261231'),timeout=60).json()
            c=r.get('archived_snapshots',{}).get('closest'); return c['timestamp'] if c else None
        except Exception: time.sleep(5)
def get(ts,url):
    for i in range(4):
        try:
            r=S.get(f'https://web.archive.org/web/{ts}id_/{url}',timeout=90)
            if r.status_code==200: return r.text
        except Exception: pass
        time.sleep(5)
def parse(html):
    i=html.find('Annual Stock Price Data')
    if i<0: return None
    t=re.sub(r'<[^>]+>',' ',html[i:i+40000]); t=re.sub(r'\s+',' ',t)
    rows={}
    for m in re.finditer(r'\b((?:19|20)\d\d) ([\d.,]+) ([\d.,]+) ([\d.,]+) ([\d.,]+) ([\d.,]+) (-?[\d.,]+)%',t):
        rows[m.group(1)]=dict(close=float(m.group(6).replace(',','')),chg=float(m.group(7).replace(',',''))/100)
    return rows
if __name__=='__main__':
    cdx=json.load(open('cdx2.json')) if os.path.exists('cdx2.json') else {}
    out=json.load(open('mt.json')) if os.path.exists('mt.json') else {}
    for t,urls in (json.loads(sys.argv[1]).items() if len(sys.argv)>1 else []):
        best=None
        for u in urls:
            full='https://www.macrotrends.net/stocks/charts/'+u
            ts=latest(full)
            if not ts: continue
            h=get(ts,full); p=parse(h) if h else None
            print(t,u,ts,len(p) if p else p, flush=True)
            if p and (best is None or ts>best[0]): best=(ts,u,p)
        if best: out[t]=dict(ts=best[0],url=best[1],rows=best[2])
        json.dump(out,open('mt.json','w'),indent=0)
