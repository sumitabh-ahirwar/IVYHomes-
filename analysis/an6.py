import json, collections
L = json.load(open("data/listings.json"))
SQM = 10.7639
# robust sqft band per bedroom from non-magichomes records (p1..p99)
band = {}
for b in range(6):
    v = sorted(x["carpet_area"] for x in L if x["website"]!="magichomes" and x["bedroom"]==b)
    lo, hi = v[max(len(v)//100-1,0)], v[min(len(v)*99//100, len(v)-1)]
    band[b] = (lo, hi)
    print(f"{b}BHK band {lo}-{hi}")

def classify(x):
    lo, hi = band[x["bedroom"]]
    c = x["carpet_area"]
    in_ft  = lo*0.8 <= c <= hi*1.25
    in_m2  = lo*0.8 <= c*SQM <= hi*1.25
    if in_m2 and not in_ft: return "sqm"
    if in_ft and not in_m2: return "sqft"
    return "ambiguous"

res = collections.Counter()
amb = []
for x in L:
    k = classify(x)
    res[(x["website"]=="magichomes", k)] += 1
    if k == "ambiguous": amb.append(x)
print("\n(is_magichomes, class):", dict(res))
print("\nambiguous:", len(amb))
for x in amb[:25]:
    print(f"  {x['listing_id']:14s} {x['website']:11s} {x['bedroom']}BHK carpet={x['carpet_area']:5d} super={x['super_built_up_area']:5d} band={band[x['bedroom']]}")
# per-bedroom gap check within magichomes
print("\n-- magichomes per-bedroom sorted carpet, gap check --")
for b in range(6):
    v = sorted(x["carpet_area"] for x in L if x["website"]=="magichomes" and x["bedroom"]==b)
    gaps = [(v[i+1]-v[i], v[i], v[i+1]) for i in range(len(v)-1)]
    gaps.sort(reverse=True)
    print(f" {b}BHK n={len(v)} range {v[0]}..{v[-1]} biggest gap {gaps[0] if gaps else None}")
