import json, collections, re, itertools
L = json.load(open("data/listings.json"))
SQM=10.7639
def is_sqm(x): return x["website"]=="magichomes" and x["carpet_area"]<300
def norm(n):
    n=n.lower().replace("-"," ").replace("_"," "); n=re.sub(r"[^a-z0-9 ]"," ",n)
    n=re.sub(r"\s+"," ",n).strip(); n=re.sub(r"^the ","",n)
    return re.sub(r" (apartments|apartment|apts)$","",n).strip()
def same_area(a,b):
    """Compare respecting each record's own unit granularity."""
    A,B = a["carpet_area"], b["carpet_area"]
    sa,sb = is_sqm(a), is_sqm(b)
    if sa==sb: return A==B                       # same unit -> exact
    if sa: return round(B/SQM)==A                 # a in m2, b in ft2
    return round(A/SQM)==B
blocks=collections.defaultdict(list)
for x in L: blocks[(norm(x["apartment_name"]),x["locality"],x["bedroom"])].append(x)
pairs=[]
for b in blocks.values():
    for a,c in itertools.combinations(b,2):
        if a["floor"]!=c["floor"]: continue
        if not same_area(a,c): continue
        # super_built_up must corroborate
        pairs.append((a,c))
print("pairs (name+loc+bed+floor+area, unit-aware):", len(pairs))
# also require super_built_up_area to corroborate
def same_sbu(a,b):
    A,B=a["super_built_up_area"],b["super_built_up_area"]; sa,sb=is_sqm(a),is_sqm(b)
    if sa==sb: return A==B
    if sa: return round(B/SQM)==A
    return round(A/SQM)==B
strict=[(a,c) for a,c in pairs if same_sbu(a,c)]
print("  ...also matching super_built_up:", len(strict))
# connected components
import collections as C
adj=C.defaultdict(set)
for a,c in pairs: adj[a["listing_id"]].add(c["listing_id"]); adj[c["listing_id"]].add(a["listing_id"])
seen=set(); comps=[]
for n in adj:
    if n in seen: continue
    st=[n]; comp=set()
    while st:
        u=st.pop()
        if u in comp: continue
        comp.add(u); seen.add(u); st.extend(adj[u]-comp)
    comps.append(comp)
print("clusters:", len(comps), "sizes:", dict(C.Counter(len(c) for c in comps)))
extra=sum(len(c)-1 for c in comps)
print("duplicate (extra) records:", extra, "=> unique properties:", len(L)-extra)
FAKE5={'+912007133812','+912007145137','+912000039837','+912007219058','+912003561453'}
byid={x["listing_id"]:x for x in L}
nf=sum(1 for c in comps for i in c if byid[i]["posted_by_contact"] in FAKE5)
print("members on FAKE5 phones:", nf)
xw=sum(1 for c in comps if len({byid[i]["website"] for i in c})>1)
print("cross-website clusters:", xw, "same-website clusters:", len(comps)-xw)
json.dump([sorted(c) for c in comps], open("data/dup_clusters.json","w"), indent=1)
