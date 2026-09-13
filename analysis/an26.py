import json, collections, re
R = json.load(open("data/rentals.json"))
P = json.load(open("data/projects.json"))
print("== project price_min > price_max ==")
bad=[x for x in P if x["price_min"]>x["price_max"]]
print(len(bad))
for x in bad[:15]: print(f"  {x['project_id']} min={x['price_min']:7.2f} max={x['price_max']:6.2f} {x['apartment_name']}")
print("\nprice_min histogram:", sorted(collections.Counter(int(x["price_min"]) for x in P).items())[:12], "...")
print("price_min >20:", sum(1 for x in P if x["price_min"]>20))
print("\n== deposit units by website ==")
for w in sorted({x["website"] for x in R}):
    rows=[x for x in R if x["website"]==w]
    rat=sorted(x["deposit"]/x["price"] for x in rows if x["price"]>0)
    dep=sorted(x["deposit"] for x in rows)
    print(f" {w:11s} deposit med={dep[len(dep)//2]:8d} min={dep[0]:6d} max={dep[-1]:9d}  dep/rent med={rat[len(rat)//2]:7.2f}")
print("\nzerobroker deposit values:", sorted(collections.Counter(x["deposit"] for x in R if x["website"]=="zerobroker").items()))
print("\n== rental title locality vs locality field ==")
LOCS=sorted({x["locality"] for x in R})
def title_loc(t):
    tl=t.lower()
    for L in LOCS:
        if L in tl: return L
    return None
tl=[(title_loc(x["title"]), x["locality"], x) for x in R]
print("title has a known locality:", sum(1 for a,b,c in tl if a))
print("matches locality field:", sum(1 for a,b,c in tl if a and a==b))
print("mismatched:", sum(1 for a,b,c in tl if a and a!=b))
print("\n== rental title BHK vs bedroom ==")
def tbhk(t):
    m=re.search(r"(\d+)\s*bhk", t.lower()); return int(m.group(1)) if m else None
bm=[(tbhk(x["title"]), x["bedroom"]) for x in R]
print("title has bhk:", sum(1 for a,b in bm if a is not None), "mismatch:", sum(1 for a,b in bm if a is not None and a!=b))
