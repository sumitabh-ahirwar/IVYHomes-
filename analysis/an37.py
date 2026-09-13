from api import *
import json, collections
a=Api()
L=json.load(open("data/listings.json"))
print("/v1/rentals/export:", a.get("/v1/rentals/export").status_code, "(NOT in the docs - not reportable as missing_endpoint)")
print()
for loc in ["chembur","powai"]:
    rows=[]; off=0
    while True:
        j=a.get("/v1/listings", limit=50, offset=off, locality=loc).json()
        rows+=j["results"]
        if j["count"]==0 or not j["has_more"]: break
        off+=j["count"]
    local=sum(1 for x in L if x["locality"]==loc)
    print(f"locality={loc}: reported total={j['total']}  fully-paged={len(rows)}  local dataset={local}  unique={len({x['listing_id'] for x in rows})}")
j=a.get("/v1/localities").json()
print("\n/v1/localities counts:", {r["locality"]:r["listing_count"] for r in j["results"]})
print("sum:", sum(r["listing_count"] for r in j["results"]))
print("matches local dataset:", {r["locality"]: r["listing_count"]==sum(1 for x in L if x["locality"]==r["locality"]) for r in j["results"]})
print("\nratio reported_total/real for each endpoint:")
for ep,real in [("/v1/listings",5100),("/v1/rentals",2100),("/v1/projects",590)]:
    t=a.get(ep, limit=1).json()["total"]
    print(f"  {ep:14s} total={t} real={real} ratio={t/real:.4f}")
