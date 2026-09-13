from api import *
import json, collections, requests
a=Api()
print("== does logout actually invalidate? ==")
tok=a.access
a.raw("POST","/auth/logout")
r=requests.get(f"{BASE}/v1/listings?limit=1", headers={"X-API-Key":KEY,"Authorization":f"Bearer {tok}"})
print("  reuse token after logout:", r.status_code, "->", "STILL VALID (doc says invalidated)" if r.status_code==200 else r.text[:100])
a=Api()
print("\n== saved list is per-user? ==")
a.raw("POST","/v1/saved", json={"listing_id":"SQU-5004678"})
b=Api("demo2@ivy.homes")
print("  demo1 saved:", a.get('/v1/saved').json()["count"], " demo2 saved:", b.get('/v1/saved').json()["count"])
a.raw("DELETE","/v1/saved/SQU-5004678")
print("\n== RENTALS filters/sorts ==")
for label,p in [("locality=chembur",{"locality":"chembur"}),("bhk=2",{"bhk":2}),
  ("furnishing=fully-furnished",{"furnishing":"fully-furnished"}),("min_price=50000",{"min_price":50000}),
  ("property_type=villa",{"property_type":"villa"})]:
    r=a.get("/v1/rentals", limit=50, **p); j=r.json(); res=j["results"]
    if "locality" in p: c=f"all match {all(x['locality']=='chembur' for x in res)}"
    elif "bhk" in p: c=f"bedrooms {sorted({x['bedroom'] for x in res})}"
    elif "furnishing" in p: c=f"furn {sorted({x['furnishing'] for x in res})}"
    elif "min_price" in p: c=f"min rent {min(x['price'] for x in res)}"
    else: c=f"types {sorted({x['property_type'] for x in res})}"
    print(f"  {label:30s} total={j['total']:5d} {c}")
for sb in ["price","carpet_area","posted_at","bedroom"]:
    r=a.get("/v1/rentals", limit=30, sort_by=sb, order="asc")
    if r.status_code!=200: print(f"  sort {sb}: {r.status_code} {r.text[:90]}"); continue
    v=[x.get(sb) for x in r.json()["results"]]
    print(f"  rentals sort_by={sb:12s} asc sorted={v==sorted(v)} {v[:5]}")
print("\n== PROJECTS filters/sorts ==")
for label,p in [("locality=chembur",{"locality":"chembur"}),("project_status=new launch",{"project_status":"new launch"})]:
    r=a.get("/v1/projects", limit=50, **p); j=r.json(); res=j["results"]
    f="locality" if "locality" in p else "project_status"
    print(f"  {label:30s} total={j['total']:5d} values={sorted({x[f] for x in res})[:4]}")
for sb in ["price_min","price_max","launch_date","total_units"]:
    r=a.get("/v1/projects", limit=30, sort_by=sb, order="desc")
    if r.status_code!=200: print(f"  sort {sb}: {r.status_code} {r.text[:110]}"); continue
    v=[x.get(sb) for x in r.json()["results"]]
    print(f"  projects sort_by={sb:12s} desc sorted={v==sorted(v,reverse=True)} {v[:4]}")
