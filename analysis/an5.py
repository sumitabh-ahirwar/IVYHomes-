import json, collections
L = json.load(open("data/listings.json"))
print("-- carpet by bedroom, NON-magichomes (p5/med/p95) --")
for b in range(6):
    v = sorted(x["carpet_area"] for x in L if x["website"]!="magichomes" and x["bedroom"]==b)
    if v: print(f" {b}BHK n={len(v):4d} min={v[0]:5d} p5={v[len(v)//20]:5d} med={v[len(v)//2]:5d} p95={v[len(v)*19//20]:5d} max={v[-1]:5d}")
M = sorted([x for x in L if x["website"]=="magichomes"], key=lambda x: x["carpet_area"])
print("\n-- magichomes boundary zone (carpet 150-450) --")
for x in M:
    if 150 <= x["carpet_area"] <= 450:
        print(f"  {x['listing_id']} {x['bedroom']}BHK carpet={x['carpet_area']:4d} super={x['super_built_up_area']:4d} x10.76={x['carpet_area']*10.7639:7.0f} proj={x['project_id']}")
