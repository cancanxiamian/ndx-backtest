import re, json
names={}
by={}
for y in range(2010,2027):
    L=open(f'wt_{y}.txt',encoding='utf8').read().splitlines()
    s=[i for i,l in enumerate(L) if re.match(r'^=+\s*(Current )?Components\s*=+',l.strip(),re.I)][0]
    e=next(i for i in range(s+1,len(L)) if re.match(r'^==',L[i].strip()))
    for l in L[s+1:e]:
        l=l.strip()
        def nm(x):
            m=re.search(r'\[\[([^\]]+)\]\]',x)
            if not m: return None
            v=m.group(1).split('|')[-1]
            return re.sub(r',? (Inc\.?|Incorporated|Corporation|Corp\.?|Ltd\.?|plc|N\.V\.|Co\.)$','',v).strip()
        m=re.match(r'^[#*](.*)\(([A-Z.]{1,6})\)\s*$',l)
        if m and nm(m.group(1)): by.setdefault(y,{})[m.group(2).replace('.','-')]=nm(m.group(1)); continue
        if l.startswith('|') and not l.startswith(('|-','|}','{|')):
            cells=[c.strip() for c in re.split(r'\|\|',l.lstrip('|'))]
            tk=next((re.sub(r'\{\{[^|}]*\|([^}]*)\}\}',r'\1',c) for c in cells if re.fullmatch(r'[A-Z][A-Z.]{0,5}',re.sub(r'\{\{[^|}]*\|([^}]*)\}\}',r'\1',c))),None)
            n=next((nm(c) for c in cells if '[[' in c),None)
            if tk and n: by.setdefault(y,{})[tk.replace('.','-')]=n
json.dump(by,open("names.json","w"),indent=0,ensure_ascii=False)
print({y:len(v) for y,v in by.items()}, by[2014].get("FOXA"), by[2012].get("PCLN"))
