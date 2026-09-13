import json, collections
R = json.load(open("data/rentals.json"))
P = json.load(open("data/projects.json"))
print("== RENTALS ==")
print("websites:", collections.Counter(x["website"] for x in R))
print("is_live:", collections.Counter(x["is_live"] for x in R))
print("localities:", collections.Counter(x["locality"] for x in R).most_common())
for w in sorted({x["website"] for x in R}):
    v=sorted(x["carpet_area"] for x in R if x["website"]==w)
    p=sorted(x["price"] for x in R if x["website"]==w)
    d=sorted(x["deposit"] for x in R if x["website"]==w)
    print(f" {w:11s} n={len(v):4d} carpet med={v[len(v)//2]:5d} min={v[0]:4d} | rent med={p[len(p)//2]:8d} min={p[0]:7d} max={p[-1]:9d} | dep med={d[len(d)//2]:9d}")
print("\nrent histogram (log-ish):")
h=collections.Counter()
for x in R:
    pr=x["price"]
    b = "<1000" if pr<1000 else "1k-10k" if pr<10000 else "10k-100k" if pr<100000 else "100k-1M" if pr<1000000 else ">=1M"
    h[b]+=1
print(" ", dict(h))
print("\ndeposit/rent ratio:", sorted(round(x['deposit']/x['price'],1) for x in R if x['price']>0)[::len(R)//10][:12])
print("\ntitle-vs-locality mismatch:")
mm=[x for x in R if x["title"] and x["locality"] and x["locality"].split()[0] not in x["title"].lower()]
print("  ", len(mm), "of", len(R))
print("\n== PROJECTS ==")
pmin=sorted(x["price_min"] for x in P); pmax=sorted(x["price_max"] for x in P)
print("price_min range:", pmin[0], pmin[len(pmin)//2], pmin[-1])
print("price_max range:", pmax[0], pmax[len(pmax)//2], pmax[-1])
print("types:", collections.Counter(type(x["price_max"]).__name__ for x in P))
print("status:", collections.Counter(x["project_status"] for x in P))
print("total_listings sum:", sum(x["total_listings"] for x in P))
print("min_area/max_area:", sorted(x["min_area_sqft"] for x in P)[:3], sorted(x["max_area_sqft"] for x in P)[-3:])
top=sorted(P, key=lambda x:-x["price_max"])[:5]
for x in top: print(f"  {x['project_id']} price_max={x['price_max']} price_min={x['price_min']} {x['apartment_name']}")
