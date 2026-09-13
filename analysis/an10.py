import json, collections
L = json.load(open("data/listings.json"))
c = collections.Counter(x["posted_by_contact"] for x in L)
SQM=10.7639
def band_ppsf(x):
    ca = x["carpet_area"]
    if x["website"]=="magichomes" and ca < 300: ca = ca*SQM
    return x["price"]/ca if ca>0 else 0
med_ppsf = sorted(band_ppsf(x) for x in L if x["price"]>0)
med = med_ppsf[len(med_ppsf)//2]
print("global median Rs/sqft (sqm-corrected):", round(med))
for phone, n in c.most_common(14):
    rows = [x for x in L if x["posted_by_contact"]==phone]
    pps = sorted(band_ppsf(x) for x in rows if x["price"]>0)
    names = collections.Counter(x["posted_by_name"] for x in rows)
    sites = collections.Counter(x["website"] for x in rows)
    pb = collections.Counter(x["posted_by"] for x in rows)
    live = collections.Counter(x["is_live"] for x in rows)
    ver = collections.Counter(x["is_verified"] for x in rows)
    print(f"\n{phone} n={n} medPPSF={pps[len(pps)//2]:.0f} ({pps[len(pps)//2]/med*100:.0f}% of mkt)")
    print(f"   names={dict(names)} sites={dict(sites)} posted_by={dict(pb)} live={dict(live)} verified={dict(ver)}")
