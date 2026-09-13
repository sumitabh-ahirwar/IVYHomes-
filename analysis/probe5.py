from api import *
a = Api()
for ep in ["/v1/listings", "/v1/rentals", "/v1/projects"]:
    lo, hi = 0, 1
    # exponential search for first offset where has_more is False / count==0
    while True:
        r = a.get(ep, limit=1, offset=hi)
        j = r.json()
        if j["count"] == 0 or not j["has_more"]:
            break
        lo = hi; hi *= 2
        if hi > 200000: break
    # binary search smallest offset with count==0
    lo2, hi2 = lo, hi
    while lo2 < hi2:
        mid = (lo2 + hi2)//2
        j = a.get(ep, limit=1, offset=mid).json()
        if j["count"] == 0: hi2 = mid
        else: lo2 = mid+1
    r = a.get(ep, limit=1, offset=max(lo2-1,0)).json()
    print(f"{ep}: reported total={r['total']}  REAL count={lo2}  (last has_more={r['has_more']})")
print("calls", a.calls)
