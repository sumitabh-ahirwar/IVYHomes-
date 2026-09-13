from api import *
import json, collections
a=Api()
def probe(ep, label, **p):
    r=a.get(ep, limit=50, **p)
    if r.status_code!=200: return print(f"  {label:44s} HTTP {r.status_code} {r.text[:110]}")
    j=r.json(); res=j["results"]
    return j, res
print("== LISTINGS filters ==")
for label,p in [("locality=chembur",{"locality":"chembur"}),("locality=Chembur",{"locality":"Chembur"}),
  ("bhk=2",{"bhk":2}),("bedroom=2",{"bedroom":2}),("property_type=villa",{"property_type":"villa"}),
  ("furnishing=unfurnished",{"furnishing":"unfurnished"}),("min_price=50000000",{"min_price":50000000}),
  ("max_price=10000000",{"max_price":10000000}),("project_id=P50001",{"project_id":"P50001"}),
  ("is_live=true",{"is_live":"true"}),("is_live=false",{"is_live":"false"}),("bogus_param=xyz",{"bogus_param":"xyz"})]:
    out=probe("/v1/listings", label, **p)
    if not out: continue
    j,res=out
    checks=""
    if "locality" in p: checks=f"all match: {all(x['locality']==p['locality'].lower() for x in res)}"
    if "bhk" in p: checks=f"bedrooms seen: {sorted({x['bedroom'] for x in res})}"
    if "bedroom" in p: checks=f"bedrooms seen: {sorted({x['bedroom'] for x in res})}"
    if "property_type" in p: checks=f"types: {sorted({x['property_type'] for x in res})}"
    if "furnishing" in p: checks=f"furn: {sorted({x['furnishing'] for x in res})}"
    if "min_price" in p: checks=f"min price seen: {min(x['price'] for x in res)}"
    if "max_price" in p: checks=f"max price seen: {max(x['price'] for x in res)}"
    if "project_id" in p: checks=f"projects: {sorted({str(x['project_id']) for x in res})[:4]}"
    if "is_live" in p: checks=f"is_live: {collections.Counter(x['is_live'] for x in res)}"
    print(f"  {label:44s} total={j['total']:5d} n={len(res):3d} {checks}")
print("\n== LISTINGS sorting ==")
for sb in ["price","carpet_area","posted_at","bedroom","bogus"]:
    for od in ["asc","desc"]:
        out=probe("/v1/listings", f"sort_by={sb}&order={od}", sort_by=sb, order=od)
        if not out: continue
        j,res=out
        f=sb if sb in res[0] else "price"
        vals=[x[f] for x in res[:8]]
        srt = vals==sorted(vals) if od=="asc" else vals==sorted(vals, reverse=True)
        print(f"  sort_by={sb:11s} order={od:4s} sorted={srt!s:5s} first8={vals[:6]}")
