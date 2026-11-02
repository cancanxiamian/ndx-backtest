import requests, json, time, os
S=requests.Session(); S.headers['User-Agent']='ndx-backtest/1.0 (personal research)'
def get(params):
    for i in range(6):
        r=S.get('https://en.wikipedia.org/w/api.php',params=params)
        try: return r.json()
        except Exception: time.sleep(3*(i+1))
    raise SystemExit('fail '+r.text[:200])
for y in range(2010,2027):
    fn=f'wt_{y}.txt'
    if os.path.exists(fn): continue
    r=get(dict(action='query',prop='revisions',titles='Nasdaq-100',rvlimit=1,rvstart=f'{y}-01-01T00:00:00Z',rvdir='older',rvprop='ids|timestamp|content',rvslots='main',format='json'))
    rv=next(iter(r['query']['pages'].values()))['revisions'][0]
    open(fn,'w',encoding='utf8').write(rv['timestamp']+'\n'+rv['slots']['main']['*'])
    print(y,rv['timestamp']); time.sleep(1.5)
