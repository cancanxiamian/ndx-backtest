import yfinance as yf, pandas as pd, numpy as np, warnings, logging
warnings.filterwarnings('ignore'); logging.getLogger('yfinance').setLevel(logging.CRITICAL)
def get(t):
    s=yf.Ticker(t).history(start='1999-01-01',end='2026-10-27',auto_adjust=True)['Close']; s.index=s.index.tz_localize(None).normalize(); return s
q=get('QQQ'); shy=get('SHY'); ief=get('IEF')
idx=q.index
rq=q.pct_change().fillna(0)
rc=shy.reindex(idx).pct_change().fillna(0)      # cash proxy: 1-3y Treasuries (0 before 2002-07)
rb=ief.reindex(idx).pct_change().fillna(0)      # 7-10y Treasuries (0 before 2002-07)
def stats(r,name,start):
    r=r[r.index>=start]; v=(1+r).cumprod()
    yrs=(v.index[-1]-v.index[0]).days/365.25
    dd=(v/v.cummax()-1).min()
    yr=(1+r).groupby(r.index.year).prod()-1
    return dict(策略=name,倍数=round(v.iloc[-1],2),年化=f'{(v.iloc[-1]**(1/yrs)-1)*100:.1f}%',最大回撤=f'{dd*100:.0f}%',最差年份=f'{yr.idxmin()} {yr.min()*100:+.0f}%')
# 200-day SMA, signal at close, act next day
sma200=q.rolling(200).mean(); in200=(q>sma200).shift(1).fillna(False)
r200=np.where(in200,rq,rc); r200=pd.Series(r200,idx)
# 10-month SMA on month-end closes, held the whole next month
me=q.resample('ME').last(); sig=(me>me.rolling(10).mean())
# 月末信号从下一个交易日起生效（旧写法 sig.shift(1).reindex(...) 会多滞后一个月，已修正）
pm=sig.reindex(idx,method='ffill').shift(1).fillna(False)
r10=pd.Series(np.where(pm,rq,rc),idx)
# 60/40 QQQ/IEF rebalanced every January
def mix(w):
    out=[];wq=w;val=1.0;hq=w;hb=1-w;last=None
    for d,a,b in zip(idx,rq,rb):
        if last is not None and d.year!=last: tot=hq+hb; hq,hb=tot*w,tot*(1-w)
        p=hq+hb; hq*=1+a; hb*=1+b; out.append((hq+hb)/p-1); last=d.year
    return pd.Series(out,idx)
r60=mix(0.6)
for start in ['1999-12-31','2010-12-31']:
    print('==== 起点',start)
    for r,n in [(rq,'一直持有 QQQ'),(r200,'200日均线过滤'),(r10,'10个月均线过滤'),(r60,'60% QQQ + 40% 中期国债，每年再平衡')]:
        print(stats(r,n,start))
sw=(in200.astype(int).diff().abs().sum()); sm=(sig.astype(int).diff().abs().sum())
print('切换次数 200日:',int(sw),' 10个月:',int(sm))
print('数据截至',idx[-1].date())
