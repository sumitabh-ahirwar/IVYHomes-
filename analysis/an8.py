import json, collections
L = json.load(open("data/listings.json"))
sw = [x for x in L if x["latitude"]>73]
print("lat>73 records (n=%d):" % len(sw))
for x in sw: print(f"  {x['listing_id']} lat={x['latitude']} lon={x['longitude']} loc={x['locality']}")
print("\nlon distribution:")
v = sorted(x["longitude"] for x in L)
print("  min", v[:3], "p1", v[len(v)//100], "med", v[len(v)//2], "p99", v[len(v)*99//100], "max", v[-3:])
b = collections.Counter(round(x["longitude"],1) for x in L)
print(" ", sorted(b.items()))
print("\nlat distribution:")
b = collections.Counter(round(x["latitude"],1) for x in L)
print(" ", sorted(b.items()))
print("\nlon>73.0 by locality:", collections.Counter(x["locality"] for x in L if x["longitude"]>73.0).most_common())
print("\n-- per-locality lat/lon centroid spread --")
for loc in sorted({x["locality"] for x in L}):
    la = sorted(x["latitude"] for x in L if x["locality"]==loc and x["latitude"]<73)
    lo = sorted(x["longitude"] for x in L if x["locality"]==loc and x["longitude"]>19)
    print(f" {loc:16s} lat {la[0]:.3f}-{la[-1]:.3f} lon {lo[0]:.3f}-{lo[-1]:.3f}")
