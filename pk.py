"""股票 PK 标签页的数据：把 px.pkl 的日线复权收盘价打包成 pk_prices.json 和 pk_calendar.json。
- 排除没有数据的列，以及代码被别的公司重新使用、Yahoo 数据已不属于原公司的列（BAD 里为 9999 的，SNDK 除外：那是 2025 年分拆的新 Sandisk）。
- 每只股票一行：c 是从 first 那天起每个交易日的 round(ln(价格)×10000) 的逐日差，空值记为空串（停牌/缺数据），
  页面累加回去即得到对数价格，误差不超过 0.5 个基点，不会累积。
- 价格是含分红的复权价，只能看涨跌幅，不能看价格本身（px.pkl 的绝对价位有缩放）。"""
import json, math, numpy as np, pandas as pd
from bt2 import d, BAD, names, LAST
NAME = {}
for y in sorted(names): NAME.update(names[y])
NAME.update({'QQQ': 'Invesco QQQ（纳斯达克100 ETF）', 'INSM': 'Insmed', 'BB': 'BlackBerry', 'WTW': 'Willis Towers Watson', 'GEN': 'Gen Digital',
             'FWONA': 'Liberty Formula One（A 类）', 'FWONK': 'Liberty Formula One（C 类）', 'VTRS': 'Viatris', 'BATRA': 'Atlanta Braves Holdings（A 类）',
             'BATRK': 'Atlanta Braves Holdings（C 类）', 'SMCI': 'Super Micro Computer', 'SOLS': 'Solstice Advanced Materials',
             'FOXA': 'Fox Corporation（A 类）', 'FOX': 'Fox Corporation（B 类）', 'NWSA': 'News Corp（A 类）', 'NWS': 'News Corp（B 类）',
             'DELL': 'Dell Technologies', 'SNDK': 'Sandisk（2025 年从西部数据分拆）', 'GOOGL': 'Alphabet（A 类）', 'GOOG': 'Alphabet（C 类）'})
keep = [t for t in d.columns if d[t].notna().any() and not (BAD.get(t) == 9999 and t != 'SNDK')]
cal = d.index
rows = []
for t in keep:
    s = d[t]; first = s.first_valid_index(); last = s.last_valid_index()
    s = s[first:last]
    L = np.round(np.log(s.values) * 10000)
    out, prev = [], None
    for x in L:
        if np.isnan(x): out.append(''); continue
        out.append(str(int(x if prev is None else x - prev))); prev = x
    rows.append(dict(ticker=t, name=NAME.get(t, t), first=str(first.date()), last=str(last.date()), days=int(s.notna().sum()), c=','.join(out)))
rows.sort(key=lambda r: (r['ticker'] != 'QQQ', r['ticker']))
json.dump(rows, open('pk_prices.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump([{'d': str(x.date())} for x in cal], open('pk_calendar.json', 'w'), separators=(',', ':'))
if __name__ == '__main__':
    import os
    print(len(rows), 'tickers', os.path.getsize('pk_prices.json') // 1024, 'KB', os.path.getsize('pk_calendar.json') // 1024, 'KB', 'to', LAST.date())
    # 校验：解码后和原价的对数误差
    r = next(x for x in rows if x['ticker'] == 'NVDA'); acc, back = 0, []
    for i, v in enumerate(r['c'].split(',')):
        if v == '': back.append(np.nan); continue
        acc += int(v); back.append(acc)
    s = d['NVDA'][r['first']:r['last']]; err = np.nanmax(np.abs(np.array(back) / 1e4 - np.log(s.values)))
    print('NVDA max log err', err, 'total return', math.exp(back[-1] / 1e4 - back[0] / 1e4) - 1, s.iloc[-1] / s.iloc[0] - 1)
