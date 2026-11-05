"""“恐慌时买入”标签页的数据：panic_daily.json，每个交易日一行。
来源（云端连不上 Yahoo/Cboe/FRED，以下都是 GitHub 上别人转存的副本，已交叉核对，原始文件在 data_src/）：
- VIX：vix.csv（github.com/datasets/finance-vix，转存自 Cboe），1990-01-02 起
- VXN：vxn.csv（Cboe 历史文件 + FRED VXNCLS），2001-02-02 起
- QQQ：data_src/qqq_sixianli.csv（github.com/Sixian-Li/plain-backtest，含分红复权，与 px.pkl 的 QQQ 一致），
       之后接 px.pkl（Yahoo 复权），再接 data_src/qqq_yennanliu.csv（github.com/yennanliu/finance_data，只复权拆股）
- 标普500：data_src/spy_sixianli.csv（同上仓库，SPY 含分红复权，与 fja05680/brownbear 的 Adj Close 一致）
- 费城半导体：SOXX，data_src/soxx_testhound.csv（github.com/testhound/palvalidator）接 data_src/soxx_yennanliu.csv，
       两者重叠部分逐日一致；只复权拆股，不含分红
拼接方法：后一段从前一段最后一天起按日收益率接上。
vix_p / vxn_p：当天收盘在过去 3 年（756 个交易日，含当天）里的百分位（比它低的天数占比），只用过去的数据。"""
import json, numpy as np, pandas as pd
def chain(*parts):
    out = parts[0].dropna()
    for p in parts[1:]:
        p = p.dropna(); p = p[p.index >= out.index[-1]]
        if len(p) < 2: continue
        out = pd.concat([out, out.iloc[-1] * p.iloc[1:] / p.iloc[0]])
    return out[~out.index.duplicated()]
rd = lambda f, dc, vc, fmt=None: pd.read_csv(f).assign(_d=lambda x: pd.to_datetime(x[dc], format=fmt)).set_index('_d')[vc].astype(float)
vix = pd.read_csv('vix.csv', index_col=0, parse_dates=True)['CLOSE']
vxn = pd.read_csv('vxn.csv', index_col=0, parse_dates=True)['close']
qqq = chain(rd('data_src/qqq_sixianli.csv', 'date', 'close'), pd.read_pickle('px.pkl')['QQQ'], rd('data_src/qqq_yennanliu.csv', 'date', 'close'))
spy = rd('data_src/spy_sixianli.csv', 'date', 'close')
soxx = chain(rd('data_src/soxx_testhound.csv', 'Date/Time', 'Close', '%m/%d/%Y'), rd('data_src/soxx_yennanliu.csv', 'date', 'close'))
# 交易日历：QQQ 或 SPY 有收盘价的日子。各来源在休市日残留的行（如 VIX 的假日行）一律去掉，再算百分位
mkt = qqq.index.union(spy.index)
mkt = mkt[mkt.weekday < 5]
vix, vxn, soxx = vix[vix.index.isin(mkt)], vxn[vxn.index.isin(mkt)], soxx[soxx.index.isin(mkt)]
pct = lambda s: s.rolling(756).apply(lambda a: (a[:-1] < a[-1]).mean() * 100, raw=True)
vix_p, vxn_p = pct(vix), pct(vxn)
cal = mkt[mkt >= '1999-03-10']
df = pd.DataFrame({'vix': vix, 'vxn': vxn, 'qqq': qqq, 'spy': spy, 'soxx': soxx, 'vix_p': vix_p, 'vxn_p': vxn_p}).reindex(cal)
# 只在有交易的日子保留价格（不同来源的假日不一致时不前向填充，避免假的零收益）
rows = []
for d, r in df.iterrows():
    o = {'d': str(d.date())}
    for k in ('vix', 'vxn'): o[k] = None if np.isnan(r[k]) else round(float(r[k]), 2)
    for k in ('qqq', 'spy', 'soxx'): o[k] = None if np.isnan(r[k]) else float(f'{r[k]:.6g}')
    for k in ('vix_p', 'vxn_p'): o[k] = None if np.isnan(r[k]) else round(float(r[k]), 1)
    rows.append(o)
json.dump(rows, open('panic_daily.json', 'w'), separators=(',', ':'))
if __name__ == '__main__':
    import os
    print(len(rows), 'rows', rows[0]['d'], '→', rows[-1]['d'], os.path.getsize('panic_daily.json') // 1024, 'KB')
    for k in ('vix', 'vxn', 'qqq', 'spy', 'soxx', 'vix_p', 'vxn_p'):
        s = df[k].dropna(); print(f'{k:6s} {s.index[0].date()} → {s.index[-1].date()} n={len(s)}')
    # 抽查：2020-03-16 前后
    print(df.loc['2020-03-13':'2020-03-17'])
