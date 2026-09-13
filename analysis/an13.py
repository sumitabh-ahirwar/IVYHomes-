import json, collections, re
L = json.load(open("data/listings.json"))
FAKE5 = {'+912007133812','+912007145137','+912000039837','+912007219058','+912003561453'}
BAIT = [
 "site visit only after the booking amount is paid",
 "below market price, this week only",
 "pay a token amount of rs 25,000 today to block the unit",
 "price negotiable for a quick sale",
 "urgent sale - owner relocating",
 "owner moving abroad, priced to sell",
]
hits = collections.Counter()
by_listing = collections.defaultdict(list)
for x in L:
    d = x["description"].lower()
    for b in BAIT:
        if b in d:
            hits[b]+=1; by_listing[x["listing_id"]].append(b)
for b,c in hits.most_common(): print(f"{c:5d}  {b}")
baited = set(by_listing)
print("\nlistings with >=1 bait phrase:", len(baited))
print("of those, phone in FAKE5:", sum(1 for i in baited if next(x for x in L if x['listing_id']==i)['posted_by_contact'] in FAKE5))
f5ids = {x["listing_id"] for x in L if x["posted_by_contact"] in FAKE5}
print("FAKE5 listings:", len(f5ids))
print("bait-but-not-FAKE5:", len(baited - f5ids))
print("FAKE5-but-no-bait:", len(f5ids - baited))
print("\nphones of baited listings:", collections.Counter(x["posted_by_contact"] for x in L if x["listing_id"] in baited).most_common())
