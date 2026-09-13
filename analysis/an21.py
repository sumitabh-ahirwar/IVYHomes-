import json, collections, re, itertools
L = json.load(open("data/listings.json"))
SQM=10.7639
def is_sqm(x): return x["website"]=="magichomes" and x["carpet_area"]<300
def norm(n):
    n=n.lower().replace("-"," ").replace("_"," "); n=re.sub(r"[^a-z0-9 ]"," ",n)
    n=re.sub(r"\s+"," ",n).strip(); n=re.sub(r"^the ","",n)
    return re.sub(r" (apartments|apartment|apts)$","",n).strip()
def area_eq(a,b,f):
    A,B=a[f],b[f]; sa,sb=is_sqm(a),is_sqm(b)
    if sa==sb: return A==B
    if sa: return round(B/SQM)==A
    return round(A/SQM)==B
# block on locality+bedroom only (looser) to not presuppose the name rule
blocks=collections.defaultdict(list)
for x in L: blocks[(x["locality"],x["bedroom"],x["floor"])].append(x)
ATTRS=["bathroom","balcony","total_floors","facing_direction","covered_parking","property_type","furnishing","posted_by"]
rows=[]
for b in blocks.values():
    for a,c in itertools.combinations(b,2):
        if not area_eq(a,c,"carpet_area"): continue
        s=sum(1 for f in ATTRS if a[f]==c[f])
        rows.append((s, area_eq(a,c,"super_built_up_area"), norm(a["apartment_name"])==norm(c["apartment_name"]),
                     a["latitude"]==c["latitude"] and a["longitude"]==c["longitude"], a, c))
print("candidate pairs (same loc+bed+floor+carpet):", len(rows))
print("\nattr-match-score histogram (of 8):", dict(collections.Counter(r[0] for r in rows)))
print("sbu match:", collections.Counter(r[1] for r in rows))
print("name match:", collections.Counter(r[2] for r in rows))
print("coord match:", collections.Counter(r[3] for r in rows))
print("\ncross-tab score x sbu x name x coord:")
ct=collections.Counter((r[0],r[1],r[2],r[3]) for r in rows)
for k in sorted(ct): print(f"  score={k[0]} sbu={int(k[1])} name={int(k[2])} coord={int(k[3])}: {ct[k]}")
