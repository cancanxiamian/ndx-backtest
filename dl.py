import json, yfinance as yf, pandas as pd, warnings, logging
warnings.filterwarnings('ignore'); logging.getLogger('yfinance').setLevel(logging.CRITICAL)
c=json.load(open('constituents.json'))
tk=sorted({t.replace('.','-') for v in c.values() for t in v}|{'QQQ'})
print(len(tk))
d=yf.download(tk,start='2008-12-01',end='2026-10-27',auto_adjust=True,progress=False,threads=True)['Close']
d.to_pickle('px.pkl')
miss=[t for t in tk if t not in d or d[t].dropna().empty]
print('missing',len(miss),miss)
