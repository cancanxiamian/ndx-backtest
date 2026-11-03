"""策略三：上一年涨幅前三等权 + 回撤减半 + 8% 止损。生成 s3_yearly.csv、s3_picks.csv。
候选口径同策略二：选股年年初成分股 + 当年加入指数的公司。
规则（按日收盘价判断，按当日收盘价成交）：
  - 收盘价 < 买入价 × 0.92：卖出该股剩余全部持仓（止损，减半后也适用）
  - 收盘价 < 买入后最高收盘价 × 0.80：卖出该股当前持仓的一半，每年每股最多一次
  - 卖出所得留作现金，不计利息，不加仓；年末清仓。不计手续费和税。
同一天两条都满足时按止损处理（剩余全部卖出，结果与先减半再止损相同）。
没有日线的持仓不套用规则，按全年涨跌计并标为 no_daily。
"""
import json, csv
from bt2 import c, names, yret, CLASS, DELIST, LAST, d, RENAME, BAD, ye
from s2 import rows as top1_rows

HALF_DD, STOP = 0.20, 0.08
ch = json.load(open('changes.json'))
adds = {}
for o in ch:
    if o['added']: adds.setdefault(int(o['date'][:4]), []).append((o['added'].replace('.', '-'), o['date'], o['added_name']))
s1y = {r['hold_year']: r['strategy_return'] for r in csv.DictReader(open('yearly.csv', encoding='utf8'))}
s2y = {r['hold_year']: r['hold_return'] for r in top1_rows}


def daily(t, H):
    """持有年的日收盘价（买入价为上一年最后一个收盘价）；没有可靠日线时返回 None"""
    t2 = RENAME.get(t, t)
    if t2 not in d or (t in BAD and t not in RENAME and H - 1 < BAD[t]): return None, None
    s = d[t2].dropna()
    buy = ye(s, H - 1)
    if buy is None: return None, None
    end = f'{H}-12-31' if H < LAST.year else str(LAST.date())
    p = s[(s.index > f'{H - 1}-12-31') & (s.index <= end)]
    if not len(p) or (H < LAST.year and p.index[-1].month != 12): return None, None
    return float(buy), p


def simulate(buy, p):
    pos, cash, peak, half, stop = 1.0, 0.0, buy, None, None
    for dt, px in p.items():
        px = float(px); peak = max(peak, px)
        if px < buy * (1 - STOP):
            cash += pos * px / buy; pos = 0.0; stop = (dt, px); break
        if half is None and px < peak * (1 - HALF_DD):
            cash += pos / 2 * px / buy; pos /= 2; half = (dt, px, peak)
    last = float(p.iloc[-1])
    return cash + pos * last / buy, half, stop, last / buy - 1


yearly, picks = [], []
for Y in range(2010, 2026):
    H = Y + 1
    uni = {t: ('年初已在指数中', names[Y].get(t, t)) for t in c[Y]}
    for t, dt, nm in adds.get(Y, []):
        if t not in uni: uni[t] = (f'{dt} 加入指数', nm)
    best = {}
    for t in uni:
        r, _ = yret(t, Y)
        if r is None or (DELIST.get(t) is not None and DELIST[t] <= Y): continue
        k = CLASS.get(t, t)
        if k not in best or r > best[k][0]: best[k] = (r, t)
    top = sorted(best.values(), reverse=True)[:3]
    vals, plain, alt, flags = [], [], [], []
    for i, (r, t) in enumerate(top):
        h, src = yret(t, H)
        buy, p = daily(t, H)
        row = dict(hold_year=H, sel_year=Y, rank=i + 1, ticker=t, company=uni[t][1], membership=uni[t][0],
                   sel_return=round(r, 4), plain_return=round(h, 4), rule_return=None, data='daily',
                   half_date='', half_vs_buy=None, half_from_peak=None, stop_date='', stop_vs_buy=None,
                   action='未触发', source=src, note='')
        if p is None:
            row.update(data='no_daily', action='无日线，无法判断',
                       note=f'没有找到 {H} 年日线（全年涨跌来自 {src}），无法判断是否触发减半或止损；汇总里按全年涨跌计入，并另算“开年即止损 −8%”情景')
            vals.append(h); alt.append(-STOP); flags.append(t)
        else:
            v, half, stop, pr = simulate(buy, p)
            assert abs(pr - h) < 2e-3, (t, H, pr, h)  # 日线与年度涨跌口径一致
            acts = []
            # 只输出相对买入价/高点的比例：px.pkl 的复权价绝对值有缩放，比例不受影响
            if half: acts.append('减半'); row.update(half_date=str(half[0].date()), half_vs_buy=round(half[1] / buy - 1, 4), half_from_peak=round(half[1] / half[2] - 1, 4))
            if stop: acts.append('止损'); row.update(stop_date=str(stop[0].date()), stop_vs_buy=round(stop[1] / buy - 1, 4))
            row.update(rule_return=round(v - 1, 4), action='+'.join(acts) or '未触发')
            vals.append(v - 1); alt.append(v - 1)
        plain.append(h); picks.append(row)
    m = lambda xs: sum(xs) / len(xs)
    yearly.append(dict(hold_year=H, s3_return=round(m(vals), 4), s3_alt_return=round(m(alt), 4) if flags else None,
                       top3_plain_return=round(m(plain), 4), s1_return=float(s1y[str(H)]), s2_return=s2y[H],
                       qqq_return=round(yret('QQQ', H)[0], 4), no_daily=' '.join(flags),
                       partial=H == LAST.year, as_of=str(LAST.date()) if H == LAST.year else f'{H}-12-31'))

if __name__ == '__main__':
    g = {k: 1.0 for k in ('s3_return', 's3_alt', 'top3_plain_return', 's1_return', 's2_return', 'qqq_return')}
    for y in yearly:
        print(y['hold_year'], ' '.join(f"{p['ticker']}:{p['action']}" for p in picks if p['hold_year'] == y['hold_year']),
              '| s3 %+.1f%% plain %+.1f%% QQQ %+.1f%%' % (y['s3_return'] * 100, y['top3_plain_return'] * 100, y['qqq_return'] * 100))
        if y['partial']: continue
        for k in g: g[k] *= 1 + (y[k] if k != 's3_alt' else (y['s3_alt_return'] if y['s3_alt_return'] is not None else y['s3_return']))
    for k, v in g.items(): print(k, 'growth %.2f cagr %.1f%%' % (v, (v ** (1 / 15) - 1) * 100))
    for fn, data in (('s3_yearly.csv', yearly), ('s3_picks.csv', picks)):
        with open(fn, 'w', newline='', encoding='utf8') as f:
            w = csv.DictWriter(f, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
