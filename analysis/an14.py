import json, collections
L = json.load(open("data/listings.json"))
by = {x["listing_id"]: x for x in L}
SQM=10.7639
def ca_ft(x):
    ca=x["carpet_area"]; return ca*SQM if (x["website"]=="magichomes" and ca<300) else ca
def ppsf(x): return x["price"]/ca_ft(x) if ca_ft(x)>0 and x["price"]>0 else None
FAKE5 = {'+912007133812','+912007145137','+912000039837','+912007219058','+912003561453'}
BAIT = ["site visit only after the booking amount is paid","below market price, this week only",
 "pay a token amount of rs 25,000 today to block the unit","price negotiable for a quick sale",
 "urgent sale - owner relocating","owner moving abroad, priced to sell"]

print("per-phrase: n, %on FAKE5 phone, median PPSF")
for b in BAIT:
    rows=[x for x in L if b in x["description"].lower()]
    f=sum(1 for x in rows if x["posted_by_contact"] in FAKE5)
    p=sorted(v for v in (ppsf(x) for x in rows) if v)
    print(f"  {b[:48]:50s} n={len(rows):4d} onFake5={f/len(rows)*100:5.1f}%  medPPSF={p[len(p)//2]:6.0f}")

f5 = [x for x in L if x["posted_by_contact"] in FAKE5]
baited = {x["listing_id"] for x in L if any(b in x["description"].lower() for b in BAIT)}
print("\n== 25 baited but NOT on a FAKE5 phone ==")
for x in L:
    if x["listing_id"] in baited and x["posted_by_contact"] not in FAKE5:
        ph=[b for b in BAIT if b in x["description"].lower()]
        print(f"  {x['listing_id']:14s} ppsf={ppsf(x) or 0:6.0f} live={x['is_live']!s:5s} ver={x['is_verified']!s:5s} by={x['posted_by']:7s} phr={len(ph)} {ph[0][:30]}")
print("\n== 37 FAKE5-phone but no bait phrase ==")
for x in f5:
    if x["listing_id"] not in baited:
        print(f"  {x['listing_id']:14s} ppsf={ppsf(x) or 0:6.0f} live={x['is_live']!s:5s} ver={x['is_verified']!s:5s} | {x['description'][:95]}")
