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
blocks=collections.defaultdict(list)
for x in L: blocks[(x["locality"],x["bedroom"],x["floor"])].append(x)
ATTRS=["bathroom","balcony","total_floors","facing_direction","covered_parking","property_type","furnishing","posted_by"]
P=[]
for b in blocks.values():
    for a,c in itertools.combinations(b,2):
        if area_eq(a,c,"carpet_area") and norm(a["apartment_name"])==norm(c["apartment_name"]): P.append((a,c))
print("name-matching pairs:", len(P))
diff=collections.Counter()
for a,c in P:
    for f in ATTRS+["super_built_up_area","price","website","posted_by_contact","posted_by_name","is_live","is_verified","project_id","description"]:
        if f=="super_built_up_area":
            if not area_eq(a,c,f): diff[f]+=1
        elif a[f]!=c[f]: diff[f]+=1
print("\nattribute disagreement counts (of %d pairs):" % len(P))
for f,n in diff.most_common(): print(f"  {f:20s} {n}")
print("\n-- 6 pairs where super_built_up differs --")
sh=0
for a,c in P:
    if not area_eq(a,c,"super_built_up_area") and sh<6:
        sh+=1
        print(f"  {a['listing_id']:14s} {a['website']:11s} ca={a['carpet_area']:5d} sbu={a['super_built_up_area']:5d} price={a['price']:10d} {a['apartment_name']}")
        print(f"  {c['listing_id']:14s} {c['website']:11s} ca={c['carpet_area']:5d} sbu={c['super_built_up_area']:5d} price={c['price']:10d} {c['apartment_name']}")
        print()
