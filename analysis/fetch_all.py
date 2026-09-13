from api import *
import json, os

def pull(ep, name, **extra):
    rows, offset, seen_meta = [], 0, []
    while True:
        r = a.get(ep, limit=50, offset=offset, **extra)
        j = r.json()
        seen_meta.append((offset, j["count"], j["total"], j["has_more"]))
        rows.extend(j["results"])
        if j["count"] == 0 or not j["has_more"]:
            break
        offset += j["count"] if j["count"] else 50
    path = os.path.join(DATA, name + ".json")
    json.dump(rows, open(path, "w"), indent=0)
    key = "project_id" if "project" in name else "listing_id"
    uniq = len({x[key] for x in rows})
    print(f"{name}: fetched {len(rows)} rows, {uniq} unique {key}, reported total={seen_meta[0][2]}")
    return rows

a = Api()
pull("/v1/listings", "listings")
pull("/v1/rentals", "rentals")
pull("/v1/projects", "projects")
print("total API calls:", a.calls)
