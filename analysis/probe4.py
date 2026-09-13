from api import *
a = Api()
def ids(r, n=3):
    j = r.json(); return [x["listing_id"] for x in j["results"][:n]]
def meta(r):
    j = r.json(); return {k: j[k] for k in ("limit","offset","count","total","has_more") if k in j}

print("-- page param --")
r1 = a.get("/v1/listings", limit=3, page=1); print("page=1", meta(r1), ids(r1))
r2 = a.get("/v1/listings", limit=3, page=2); print("page=2", meta(r2), ids(r2))
r3 = a.get("/v1/listings", limit=3, offset=3); print("offset=3", meta(r3), ids(r3))

print("-- limit caps --")
for L in [50, 100, 200, 201, 500, 1000, 5000]:
    r = a.get("/v1/listings", limit=L)
    print(f"limit={L}", meta(r), r.status_code)

print("-- deep offset --")
for o in [4000, 4800, 4820, 4821, 5000]:
    r = a.get("/v1/listings", limit=5, offset=o)
    print(f"offset={o}", r.status_code, meta(r) if r.status_code==200 else r.text[:150])
