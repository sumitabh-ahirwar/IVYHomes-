import json, collections
from datetime import datetime, timezone, timedelta
L = json.load(open("data/listings.json"))
IST = timezone(timedelta(hours=5, minutes=30))
REF = datetime(2026,9,10,0,0,0, tzinfo=IST)
def dt(s): return datetime.fromisoformat(s.replace("Z","+00:00"))

groups = {
 "price<=0":        [x for x in L if x["price"]<=0],
 "carpet>super":    [x for x in L if x["carpet_area"]>x["super_built_up_area"]],
 "floor>totfloors": [x for x in L if x["floor"]>x["total_floors"]],
 "posted_future":   [x for x in L if dt(x["posted_at"])>REF],
 "bed0_nonplot":    [x for x in L if x["bedroom"]==0 and x["property_type"]!="plot"],
 "bath0_nonplot":   [x for x in L if x["bathroom"]==0 and x["property_type"]!="plot"],
 "tf0_nonplot":     [x for x in L if x["total_floors"]==0 and x["property_type"]!="plot"],
 "plot_has_bed":    [x for x in L if x["property_type"]=="plot" and x["bedroom"]>0],
 "lat_out":         [x for x in L if not (18.85 < x["latitude"] < 19.45)],
 "lon_out":         [x for x in L if not (72.75 < x["longitude"] < 73.05)],
 "parking>5":       [x for x in L if x["covered_parking"]>5],
 "balcony>6":       [x for x in L if x["balcony"]>6],
 "floor==0_apt":    [x for x in L if x["floor"]==0 and x["property_type"]=="apartment"],
}
for k,v in groups.items():
    print(f"{k:18s} {len(v):5d}  {[x['listing_id'] for x in v[:4]]}")

print("\n-- overlaps of the 11-groups --")
elevens = {k:set(x['listing_id'] for x in v) for k,v in groups.items() if len(v)==11}
ks = list(elevens)
for i in range(len(ks)):
    for j in range(i+1, len(ks)):
        ov = elevens[ks[i]] & elevens[ks[j]]
        if ov: print(f"  {ks[i]} & {ks[j]}: {len(ov)} {sorted(ov)}")
U = set().union(*elevens.values()) if elevens else set()
print("\nunion of 11-groups:", len(U))
print("groups of exactly 11:", ks)
print("\n-- lat/lon detail --")
print("lat range", min(x['latitude'] for x in L), max(x['latitude'] for x in L))
print("lon range", min(x['longitude'] for x in L), max(x['longitude'] for x in L))
