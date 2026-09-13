"""Final duplicate detection: exact carpet-area match (unit-aware) + normalised
apartment name + locality + bedroom + floor."""
import json, collections, re, itertools
L = json.load(open("data/listings.json"))
SQM=10.7639
def is_sqm(x): return x["website"]=="magichomes" and x["carpet_area"]<300
def norm(n):
    n=n.lower().replace("-"," ").replace("_"," "); n=re.sub(r"[^a-z0-9 ]"," ",n)
    n=re.sub(r"\s+"," ",n).strip(); n=re.sub(r"^the ","",n)
    return re.sub(r" (apartments|apartment|apts)$","",n).strip()
def area_eq(a,b):
    A,B=a["carpet_area"],b["carpet_area"]; sa,sb=is_sqm(a),is_sqm(b)
    if sa==sb: return A==B
    if sa: return round(B/SQM)==A
    return round(A/SQM)==B
def build(need_floor):
    blocks=collections.defaultdict(list)
    for x in L:
        k=(norm(x["apartment_name"]),x["locality"],x["bedroom"])+((x["floor"],) if need_floor else ())
        blocks[k].append(x)
    pr=[(a,c) for b in blocks.values() for a,c in itertools.combinations(b,2) if area_eq(a,c)]
    adj=collections.defaultdict(set)
    for a,c in pr: adj[a["listing_id"]].add(c["listing_id"]); adj[c["listing_id"]].add(a["listing_id"])
    seen=set(); comps=[]
    for n in adj:
        if n in seen: continue
        st=[n]; comp=set()
        while st:
            u=st.pop()
            if u in comp: continue
            comp.add(u); seen.add(u); st.extend(adj[u]-comp)
        comps.append(sorted(comp))
    return pr, comps
for nf in (True, False):
    pr, comps = build(nf)
    extra=sum(len(c)-1 for c in comps)
    print(f"floor required={nf}: pairs={len(pr)} clusters={len(comps)} sizes={dict(collections.Counter(len(c) for c in comps))} extra={extra} unique={5100-extra}")
pr, comps = build(True)
byid={x["listing_id"]:x for x in L}
print("\n-- clusters of size>2 --")
for c in comps:
    if len(c)>2:
        for i in c:
            x=byid[i]; print(f"  {i:14s} {x['website']:11s} {x['apartment_name']:28s} fl={x['floor']:2d} ca={x['carpet_area']:5d} sbu={x['super_built_up_area']:5d} price={x['price']:10d}")
        print()
json.dump(comps, open("data/dup_clusters.json","w"), indent=1)
print("saved", len(comps), "clusters")
