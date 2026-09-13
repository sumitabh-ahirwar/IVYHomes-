import json, collections, re
L = json.load(open("data/listings.json"))
SQM=10.7639
def ca_ft(x):
    ca=x["carpet_area"]; return round(ca*SQM) if (x["website"]=="magichomes" and ca<300) else ca
def norm(n):
    n = n.lower().replace("-", " ").replace("_"," ")
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    n = re.sub(r"^the ", "", n)
    n = re.sub(r" (apartments|apartment|apts|residency towers)$", "", n)
    return n.strip()
raw = {x["apartment_name"] for x in L}
nm = collections.Counter(norm(x["apartment_name"]) for x in L)
print("raw names:", len(raw), "-> normalised:", len(nm))
# which raw names collapse together
g = collections.defaultdict(set)
for x in L: g[norm(x["apartment_name"])].add(x["apartment_name"])
multi = {k:v for k,v in g.items() if len(v)>1}
print("normalised names with >1 raw spelling:", len(multi))
for k,v in list(multi.items())[:12]: print("  ", k, "<-", sorted(v))

print("\n-- candidate dup key: (normname, locality, bedroom, floor) --")
k = collections.Counter((norm(x["apartment_name"]), x["locality"], x["bedroom"], x["floor"]) for x in L)
print("groups>1:", sum(1 for v in k.values() if v>1), "extra:", sum(v-1 for v in k.values() if v>1))
print(collections.Counter(k.values()))
