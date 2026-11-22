import json, collections, os, shutil
SRC="/tmp/dm"; OUT="/home/claude/whereismytrain/assets/data"
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT+"/tr"); os.makedirs(OUT+"/st")
def m(t):
    if not t or t=="None": return None
    h,mi,_=t.split(":"); return int(h)*60+int(mi)
stations={f["properties"]["code"]:f["properties"]["name"] for f in json.load(open(SRC+"/stations.json"))["features"]}
sc=json.load(open(SRC+"/schedules.json"))
by=collections.defaultdict(list)
for r in sc: by[r["train_number"]].append(r)
for k in by: by[k].sort(key=lambda r:r["id"])
tm=json.load(open(SRC+"/trains.json"))["features"]
meta=[]; trs=collections.defaultdict(dict); sts=collections.defaultdict(list)
for f in tm:
    p=f["properties"]; no=p["number"]
    if no not in by: continue
    rows=by[no]; stops=[]
    for i,r in enumerate(rows):
        a,d=m(r["arrival"]),m(r["departure"])
        first,last=i==0,i==len(rows)-1
        halt=1 if (first or last or a!=d) else 0
        stops.append([r["station_code"],a,d,r["day"],halt])
        stations.setdefault(r["station_code"],r["station_name"].title())
        if halt: sts[r["station_code"]].append([no,i,a,d,r["day"],len(rows)])
    trs[no[:3]][no]=stops
    meta.append([no,p["name"],p["type"],p["from_station_code"],p["to_station_code"],p["departure"][:5],p["arrival"][:5],p["distance"],p["return_train"] or ""])
    for c in ("from_station_code","to_station_code"): stations.setdefault(p[c],p[c.replace("code","name")].title())
meta.sort()
used={c for v in sts for c in [v]}|{x[3] for x in meta}|{x[4] for x in meta}
dump=lambda p,o:open(p,"w").write(json.dumps(o,separators=(",",":"),ensure_ascii=False))
dump(OUT+"/meta.json",{"s":{c:(n.title() if n.isupper() else n) for c,n in stations.items() if c in sts or c in used},"t":meta})
for k,v in trs.items(): dump(f"{OUT}/tr/{k}.json",v)
sh=collections.defaultdict(dict)
for c,v in sts.items(): sh[c[:2].upper()][c]=v
for k,v in sh.items(): dump(f"{OUT}/st/{k}.json",v)
print("trains",len(meta),"stations",len(json.load(open(OUT+"/meta.json"))["s"]),"train shards",len(trs),"station shards",len(sh))
