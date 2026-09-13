import json, collections, re
L = json.load(open("data/listings.json"))
print("-- exact lat/lon collisions --")
c = collections.Counter((x["latitude"], x["longitude"]) for x in L)
print("groups>1:", sum(1 for v in c.values() if v>1), "extra:", sum(v-1 for v in c.values() if v>1))
print(collections.Counter(c.values()))
ex = [k for k,v in c.items() if v>1][:3]
for k in ex:
    print(f"\n  coord {k}:")
    for x in L:
        if (x["latitude"],x["longitude"])==k:
            print(f"    {x['listing_id']:14s} {x['website']:11s} {x['apartment_name']:32s} {x['locality']:15s} {x['bedroom']}BHK fl={x['floor']:3d} ca={x['carpet_area']:5d} price={x['price']:10d} {x['posted_at']}")
