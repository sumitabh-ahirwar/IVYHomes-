import json, collections
L = json.load(open("data/listings.json"))
SQM=10.7639
def ca_ft(x):
    ca = x["carpet_area"]
    return ca*SQM if (x["website"]=="magichomes" and ca<300) else ca
# exclude corrupt-ish for the baseline
good = [x for x in L if x["price"]>0 and x["carpet_area"]>0 and x["carpet_area"]<=x["super_built_up_area"]]
pps = sorted(x["price"]/ca_ft(x) for x in good)
print("PPSF percentiles:", {p: round(pps[len(pps)*p//100]) for p in (1,2,3,4,5,10,25,50,75,90,99)})
h = collections.Counter(int(x["price"]/ca_ft(x)//2500)*2500 for x in good)
print("\nPPSF histogram (2500 bins):")
for k in sorted(h): print(f"  {k:6d}: {'#'*(h[k]//10)} {h[k]}")
FAKE5 = {'+912007133812','+912007145137','+912000039837','+912007219058','+912003561453'}
lowset = [x for x in good if x["price"]/ca_ft(x) < 22000]
print("\nrecords with PPSF<22000:", len(lowset))
print("  how many have a FAKE5 phone:", sum(1 for x in lowset if x["posted_by_contact"] in FAKE5))
print("  contacts:", collections.Counter(x["posted_by_contact"] for x in lowset).most_common(10))
f5 = [x for x in good if x["posted_by_contact"] in FAKE5]
print("\nFAKE5 records:", len(f5), "PPSF range:", round(min(x['price']/ca_ft(x) for x in f5)), round(max(x['price']/ca_ft(x) for x in f5)))
