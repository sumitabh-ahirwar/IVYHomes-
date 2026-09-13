import json, collections
from datetime import datetime, timezone, timedelta
L = json.load(open("data/listings.json"))
IST = timezone(timedelta(hours=5, minutes=30))
REF = datetime(2026,9,10,0,0,0, tzinfo=IST)

def dt(s): return datetime.fromisoformat(s.replace("Z","+00:00"))

checks = {
 "price <= 0":            lambda x: x["price"] is not None and x["price"] <= 0,
 "carpet_area <= 0":      lambda x: x["carpet_area"] is not None and x["carpet_area"] <= 0,
 "carpet > superbuiltup": lambda x: x["carpet_area"] and x["super_built_up_area"] and x["carpet_area"] > x["super_built_up_area"],
 "floor > total_floors":  lambda x: x["floor"] is not None and x["total_floors"] is not None and x["floor"] > x["total_floors"],
 "floor < 0":             lambda x: x["floor"] is not None and x["floor"] < 0,
 "total_floors <= 0":     lambda x: x["total_floors"] is not None and x["total_floors"] <= 0,
 "bedroom <= 0":          lambda x: x["bedroom"] is not None and x["bedroom"] <= 0,
 "bathroom <= 0":         lambda x: x["bathroom"] is not None and x["bathroom"] <= 0,
 "bathroom > bedroom+3":  lambda x: x["bathroom"] and x["bedroom"] and x["bathroom"] > x["bedroom"]+3,
 "balcony < 0":           lambda x: x["balcony"] is not None and x["balcony"] < 0,
 "parking < 0":           lambda x: x["covered_parking"] is not None and x["covered_parking"] < 0,
 "posted_at future":      lambda x: dt(x["posted_at"]) > REF,
 "carpet < 100":          lambda x: x["carpet_area"] is not None and x["carpet_area"] < 100,
 "carpet<200 & bed>=3":   lambda x: x["carpet_area"] and x["bedroom"] and x["bedroom"]>=3 and x["carpet_area"]<200,
}
for name, f in checks.items():
    hits = [x for x in L if f(x)]
    print(f"{name:24s} {len(hits):5d}  e.g. {[h['listing_id'] for h in hits[:4]]}")

print("\n-- bedroom 0 by property_type --")
print(collections.Counter(x["property_type"] for x in L if x["bedroom"]==0))
print("\n-- future posted_at values --")
fut = sorted((x["posted_at"], x["listing_id"]) for x in L if dt(x["posted_at"])>REF)
print(len(fut), fut[:10])
