from api import *
import json, collections
from datetime import datetime, timedelta, timezone
a=Api()
# full asc & desc first 150 each
asc=[];  off=0
while len(asc)<150:
    j=a.get("/v1/listings", limit=50, offset=off, sort_by="posted_at", order="asc").json()
    asc+=j["results"]; off+=50
desc=[]; off=0
while len(desc)<150:
    j=a.get("/v1/listings", limit=50, offset=off, sort_by="posted_at", order="desc").json()
    desc+=j["results"]; off+=50
print("asc[0:5] :", [x["posted_at"] for x in asc[:5]])
print("desc[0:5]:", [x["posted_at"] for x in desc[:5]])
print("asc is non-decreasing as strings?", [x['posted_at'] for x in asc]==sorted(x['posted_at'] for x in asc))
print("desc is non-increasing as strings?", [x['posted_at'] for x in desc]==sorted((x['posted_at'] for x in desc), reverse=True))
# how far out of order is asc?
ts=[datetime.fromisoformat(x["posted_at"].replace("Z","+00:00")) for x in asc]
inv=sum(1 for i in range(len(ts)-1) if ts[i]>ts[i+1])
print(f"asc inversions: {inv} of {len(ts)-1}")
spans=[(max(ts[i:i+10])-min(ts[i:i+10])).total_seconds()/3600 for i in range(0,140,10)]
print("asc local 10-window spans (h):", [round(s,1) for s in spans[:8]])
L=json.load(open("data/listings.json"))
print("\nposted_at hour-of-day histogram (all 5100):")
h=collections.Counter(int(x["posted_at"][11:13]) for x in L)
for k in range(24): print(f"  {k:02d}h {'#'*(h[k]//8)} {h[k]}")
print("\nminute distribution sample:", sorted(collections.Counter(int(x['posted_at'][14:16]) for x in L).items())[:6])
print("\nper-website hour mean:", {w: round(sum(int(x['posted_at'][11:13]) for x in L if x['website']==w)/sum(1 for x in L if x['website']==w),2) for w in sorted({x['website'] for x in L})})
