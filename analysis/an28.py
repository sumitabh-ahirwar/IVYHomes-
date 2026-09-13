from api import *
import json
from datetime import datetime, timedelta
a=Api()
SQM=10.7639
r=a.get("/v1/listings", limit=50, sort_by="carpet_area", order="asc").json()["results"]
def ft(x):
    ca=x["carpet_area"]; return ca*SQM if (x["website"]=="magichomes" and ca<300) else ca
v=[ft(x) for x in r]
print("carpet asc, converted to sqft:", [round(y) for y in v[:14]])
print("  sorted after conversion?", v==sorted(v))
print("  raw:", [x['carpet_area'] for x in r[:14]])

r=a.get("/v1/listings", limit=50, sort_by="posted_at", order="asc").json()["results"]
print("\nposted_at asc, first 14:")
for x in r[:14]:
    print(f"  {x['listing_id']:14s} {x['website']:11s} {x['posted_at']}")
print("\nsorted as-is?", [x['posted_at'] for x in r]==sorted(x['posted_at'] for x in r))
# hypothesis: some records' posted_at is IST wall-clock mislabelled as Z
def shift(x, sites):
    d=datetime.fromisoformat(x["posted_at"].replace("Z","+00:00"))
    return d - timedelta(hours=5, minutes=30) if x["website"] in sites else d
sites_all={"100acres","dwelling","magichomes","squarelane","zerobroker"}
import itertools
best=None
for k in range(len(sites_all)+1):
    for combo in itertools.combinations(sorted(sites_all), k):
        vals=[shift(x,set(combo)) for x in r]
        if vals==sorted(vals):
            print("SORTED when shifting -5:30 for:", combo); best=combo
if best is None: print("no website subset explains the order")
