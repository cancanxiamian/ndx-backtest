"""用 VIX 管理 QQQ 仓位的几种做法。只打印。
数据：QQQ 复权日线来自 px.pkl；VIX 收盘来自 github.com/datasets/finance-vix（转存自 Cboe），存为 vix.csv。
没有 VXN 数据，用 VIX 代替。信号用当天收盘，第二天生效；空仓部分按 0 收益（不计利息），不计交易费用和税。"""
import pandas as pd, numpy as np, sys
START = sys.argv[1] if len(sys.argv) > 1 else '2010-12-31'
q = pd.read_pickle('px.pkl')['QQQ'].dropna()
v = pd.read_csv('vix.csv', index_col=0, parse_dates=True)['CLOSE']
idx = q.index[(q.index <= v.index[-1])]
q, v = q[idx], v.reindex(idx).ffill()
rq = q.pct_change().fillna(0)

def run(w, name):
    w = pd.Series(w, idx).shift(1).fillna(1.0)          # 今天收盘的信号，明天的仓位
    r = (w * rq)[idx > START]
    val = (1 + r).cumprod(); yrs = (val.index[-1] - pd.Timestamp(START)).days / 365.25
    dd = (val / val.cummax() - 1).min(); y = (1 + r).groupby(r.index.year).prod() - 1
    ww = w[idx > START]
    return dict(做法=name, 倍数=round(val.iloc[-1], 2), 年化=f'{(val.iloc[-1] ** (1 / yrs) - 1) * 100:.1f}%', 最大回撤=f'{dd * 100:.0f}%',
                平均仓位=f'{ww.mean() * 100:.0f}%', y2018=f'{y.get(2018, np.nan) * 100:+.0f}%', y2020=f'{y[2020] * 100:+.0f}%',
                y2022=f'{y[2022] * 100:+.0f}%', y2025=f'{y[2025] * 100:+.0f}%', 换仓次数=int((ww.diff().abs() > 1e-9).sum()))

def band(out, back, lo=0.0, hi=1.0):
    """VIX 高于 out 时仓位降到 lo，回到 back 以下才恢复 hi"""
    pos, cur = [], hi
    for x in v:
        if x > out: cur = lo
        elif x < back: cur = hi
        pos.append(cur)
    return np.array(pos)

rows = [run(np.ones(len(idx)), '一直持有 QQQ')]
for t in (25, 30, 40): rows.append(run(band(t, t), f'VIX>{t} 空仓，<{t} 买回'))
rows.append(run(band(30, 20), 'VIX>30 空仓，<20 才买回'))
rows.append(run(np.minimum(1, 20 / v.values), '波动率目标：仓位=20/VIX，最多100%'))
rows.append(run(np.full(len(idx), 0.7), '固定 70% QQQ + 30% 现金'))
rows.append(run(band(30, 20, lo=1.0, hi=0.7), '平时 70%，VIX>30 加到 100%，<20 回 70%'))
print(f'区间 {START} 之后 到 {idx[-1].date()}，VIX 截至 {v.index[-1].date()}')
print(pd.DataFrame(rows).to_string(index=False))

if '--sens' in sys.argv:
    print('\n--- 逆向加仓的阈值敏感性（平时 70%，VIX>入 时 100%，<出 时回 70%）')
    rs = [run(np.full(len(idx), w), f'固定 {int(w*100)}%') for w in (0.7, 0.75, 0.8)]
    for a, b in ((25, 20), (30, 20), (30, 25), (35, 20), (40, 25), (40, 30)):
        rs.append(run(band(a, b, lo=1.0, hi=0.7), f'>{a} 加满，<{b} 回 70%'))
    print(pd.DataFrame(rs).to_string(index=False))
    # 2022 年 VIX>30 空仓、<20 买回 的具体操作
    p = pd.Series(band(30, 20), idx); ch = p.diff()
    print('\nVIX>30 空仓/<20 买回 在 2021-2023 的操作：')
    for d in ch[(ch != 0) & (idx > '2021-01-01') & (idx < '2023-12-31')].index:
        print(' ', d.date(), '卖出' if ch[d] < 0 else '买回', 'VIX %.1f' % v[d], 'QQQ 距前高 %+.0f%%' % ((q[d] / q[:d].max() - 1) * 100))
