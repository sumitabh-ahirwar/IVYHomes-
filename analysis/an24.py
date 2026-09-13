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
blocks=collections.defaultdict(list)
for x in L: blocks[(norm(x["apartment_name"]),x["locality"],x["bedroom"])].append(x)
floordiff=[(a,c) for b in blocks.values() for a,c in itertools.combinations(b,2)
           if area_eq(a,c) and a["floor"]!=c["floor"]]
print("pairs matching on everything but floor:", len(floordiff))
corruptfloor={x["listing_id"] for x in L if x["floor"]>x["total_floors"]}
for a,c in floordiff:
    m=[i for i in (a,c) if i["listing_id"] in corruptfloor]
    print(f"  {a['listing_id']:14s} fl={a['floor']:3d}/tf={a['total_floors']:3d} ca={a['carpet_area']:5d} | {c['listing_id']:14s} fl={c['floor']:3d}/tf={c['total_floors']:3d} ca={c['carpet_area']:5d}  corrupt={[i['listing_id'] for i in m]}")
print("\nof these pairs, how many involve a floor>total_floors record:",
      sum(1 for a,c in floordiff if a["listing_id"] in corruptfloor or c["listing_id"] in corruptfloor), "of", len(floordiff))
