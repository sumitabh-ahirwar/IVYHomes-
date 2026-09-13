from api import *
import json, requests
a=Api()
print("== api_key as query param only (no header) ==")
s=requests.Session()
r=s.get(f"{BASE}/v1/listings?api_key={KEY}&limit=1"); print("  no header, ?api_key:", r.status_code, r.text[:120])
r=s.get(f"{BASE}/v1/listings?limit=1", headers={"X-API-Key":KEY}); print("  header, no token:", r.status_code, r.text[:120])
print("\n== token header variants ==")
r=s.get(f"{BASE}/v1/listings?limit=1", headers={"X-API-Key":KEY,"Authorization":"Bearer bogus"}); print("  bogus token:", r.status_code, r.text[:130])
print("\n== /auth/refresh ==")
r=a.raw("POST","/auth/refresh", json={"refresh_token":a.refresh}); print("  refresh:", r.status_code, r.text[:200])
print("\n== /auth/logout ==")
for p in ["/auth/logout","/v1/auth/logout"]:
    r=a.raw("POST",p); print(f"  {p}: {r.status_code} {r.text[:120]}")
print("\n== /v1/saved lifecycle ==")
for body in [{"id":"SQU-5004678"},{"listing_id":"SQU-5004678"}]:
    r=a.raw("POST","/v1/saved", json=body); print(f"  POST {body}: {r.status_code} {r.text[:160]}")
r=a.get("/v1/saved"); print("  GET:", r.status_code, r.text[:220])
for p in ["/v1/saved/SQU-5004678"]:
    r=a.raw("DELETE",p); print(f"  DELETE {p}: {r.status_code} {r.text[:140]}")
r=a.get("/v1/saved"); print("  GET after delete:", r.status_code, r.text[:160])
print("\n== errors ==")
for path,params in [("/v1/listings",{"limit":"abc"}),("/v1/listings",{"limit":-5}),("/v1/listings",{"offset":-1}),
                    ("/v1/listings/NOPE",{}),("/v1/projects/NOPE",{}),("/v1/listings",{"sort_by":"price","order":"sideways"})]:
    r=a.get(path, **params); print(f"  {path} {params}: {r.status_code} {r.text[:150]}")
