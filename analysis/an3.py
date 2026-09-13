import json, collections, statistics as st
L = json.load(open("data/listings.json"))
print("-- carpet_area by website (median, p5, p95) --")
for w in sorted({x["website"] for x in L}):
    v = sorted(x["carpet_area"] for x in L if x["website"]==w)
    print(f"{w:12s} n={len(v):5d} p5={v[len(v)//20]:6d} med={v[len(v)//2]:6d} p95={v[len(v)*19//20]:6d}")
print("\n-- ratio super_built_up/carpet by website --")
for w in sorted({x["website"] for x in L}):
    v = sorted(x["super_built_up_area"]/x["carpet_area"] for x in L if x["website"]==w and x["carpet_area"]>0)
    print(f"{w:12s} med_ratio={v[len(v)//2]:.3f}")
print("\n-- super_built_up by website --")
for w in sorted({x["website"] for x in L}):
    v = sorted(x["super_built_up_area"] for x in L if x["website"]==w)
    print(f"{w:12s} med={v[len(v)//2]:6d}")
print("\n-- price/carpet (Rs/sqft) by website --")
for w in sorted({x["website"] for x in L}):
    v = sorted(x["price"]/x["carpet_area"] for x in L if x["website"]==w and x["carpet_area"]>0 and x["price"]>0)
    print(f"{w:12s} med={v[len(v)//2]:9.0f}")
print("\n-- price median by website --")
for w in sorted({x["website"] for x in L}):
    v = sorted(x["price"] for x in L if x["website"]==w and x["price"]>0)
    print(f"{w:12s} med={v[len(v)//2]:12d}")
