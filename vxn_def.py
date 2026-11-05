"""比较几种“VXN 偏高”的定义：信号出现后 QQQ 未来 3/6/12 个月的表现。只打印。
VXN 来自 vxn.csv，QQQ 复权日线来自 px.pkl。所有信号只用当天及以前的数据。"""
import pandas as pd, numpy as np, sys
# 用法：python vxn_def.py [vxn|vix] [结束日期]；两者对比时用同一个结束日期
SRC = sys.argv[1] if len(sys.argv) > 1 else 'vxn'
END = sys.argv[2] if len(sys.argv) > 2 else None
q = pd.read_pickle('px.pkl')['QQQ'].dropna()
x = (pd.read_csv('vxn.csv', index_col=0, parse_dates=True)['close'] if SRC == 'vxn'
     else pd.read_csv('vix.csv', index_col=0, parse_dates=True)['CLOSE'])
if END: x = x[:END]
full = x.copy()                                   # VXN 2001 年起、VIX 1990 年起，用来算滚动统计
idx = q.index.intersection(x.index); q = q[idx]
def roll_pct(s, w):
    return s.rolling(w).apply(lambda a: (a[:-1] < a[-1]).mean() * 100, raw=True)
lx = np.log(full)
rv = np.log(q).diff().rolling(21).std() * np.sqrt(252) * 100     # QQQ 过去 21 天的实际波动（年化 %）
dd = q / q.rolling(252, min_periods=1).max() - 1
D = pd.DataFrame(index=idx)
D['A 数值 >30'] = x[idx] > 30
D['A2 数值 >25'] = x[idx] > 25
D['B 1年百分位≥90'] = roll_pct(full, 252)[idx] >= 90
D['C 3年百分位≥90'] = roll_pct(full, 756)[idx] >= 90
D['D 1年Z分数≥1.5'] = ((lx - lx.rolling(252).mean()) / lx.rolling(252).std())[idx] >= 1.5
D['E 突升：比60日均值高30%'] = (full / full.rolling(60).mean())[idx] >= 1.3
D['F 恐慌溢价：指数/实际波动 前10%'] = roll_pct((x[idx] / rv).dropna(), 756).reindex(idx) >= 90
D['G 双条件：QQQ距1年高点≤-15% 且 3年百分位≥80'] = (dd <= -0.15) & (roll_pct(full, 756)[idx] >= 80)
start = '2010-01-01'
H = {'3个月': 63, '6个月': 126, '12个月': 252}
fwd = {k: q.shift(-h) / q - 1 for k, h in H.items()}
def episodes(sig):
    on = sig[sig].index; n, last = 0, None
    for t in on:
        if last is None or (q.index.get_loc(t) - q.index.get_loc(last)) > 21: n += 1
        last = t
    return n
rows = []
base = {'定义': '全部交易日（对照）', '信号天数占比': '100%', '独立事件数': '—'}
for k in H: f = fwd[k][start:].dropna(); base[f'{k}平均'] = f'{f.mean()*100:+.1f}%'; base[f'{k}上涨比例'] = f'{(f>0).mean()*100:.0f}%'
f = fwd['12个月'][start:].dropna(); base['12个月最差'] = f'{f.min()*100:+.0f}%'
rows.append(base)
for name in D:
    s = D[name][start:].fillna(False).astype(bool)
    r = {'定义': name, '信号天数占比': f'{s.mean()*100:.0f}%', '独立事件数': episodes(s)}
    for k in H:
        f = fwd[k][start:][s].dropna(); r[f'{k}平均'] = f'{f.mean()*100:+.1f}%'; r[f'{k}上涨比例'] = f'{(f>0).mean()*100:.0f}%'
    f = fwd['12个月'][start:][s].dropna(); r['12个月最差'] = f'{f.min()*100:+.0f}%' if len(f) else '—'
    rows.append(r)
pd.set_option('display.width', 250); pd.set_option('display.unicode.east_asian_width', True)
print(f'[{SRC.upper()}] 信号区间 {start} 至 {idx[-1].date()}；未来收益算到 {q.index[-1].date()}，最后 12 个月的信号没有完整的 12 个月收益')
print(pd.DataFrame(rows).to_string(index=False))
