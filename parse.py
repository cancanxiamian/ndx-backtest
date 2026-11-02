import re, json
res={}
for y in range(2010,2027):
    L=open(f'wt_{y}.txt',encoding='utf8').read().splitlines()
    s=[i for i,l in enumerate(L) if re.match(r'^=+\s*(Current )?Components\s*=+',l.strip(),re.I)][0]
    e=next(i for i in range(s+1,len(L)) if re.match(r'^==',L[i].strip()))
    tk=[]
    for l in L[s+1:e]:
        l=l.strip()
        m=re.match(r'^[#*].*\(([A-Z.]{1,6})\)\s*$',l)
        if m: tk.append(m.group(1)); continue
        if l.startswith('|') and not l.startswith(('|-','|}','{|')):
            cells=[re.sub(r'\{\{[^|}]*\|([^}]*)\}\}',r'\1',c).strip() for c in re.split(r'\|\|',l.lstrip('|'))]
            for c in cells:
                if re.fullmatch(r'[A-Z][A-Z.]{0,5}',c): tk.append(c); break
    res[y]=tk
    print(y,len(tk),len(set(tk)),tk[:5])
json.dump(res,open('constituents.json','w'),indent=0)
