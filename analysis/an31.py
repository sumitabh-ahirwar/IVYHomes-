import json, collections
L=json.load(open("data/listings.json")); P=json.load(open("data/projects.json"))
raw=json.load(open("data/answers_raw.json"))
fake=set(raw["answers"]["fake_listing_ids"]); corrupt=set(raw["answers"]["corrupt_listing_ids"])
dupdrop=set()
for c in raw["dup_clusters"]: dupdrop|=set(c[1:])
defs={
 "all records":      lambda x: True,
 "is_live only":     lambda x: x["is_live"],
 "live & !fake":     lambda x: x["is_live"] and x["listing_id"] not in fake,
 "!fake":            lambda x: x["listing_id"] not in fake,
 "live & !fake & !corrupt": lambda x: x["is_live"] and x["listing_id"] not in fake and x["listing_id"] not in corrupt,
 "live & deduped":   lambda x: x["is_live"] and x["listing_id"] not in dupdrop,
 "all & deduped":    lambda x: x["listing_id"] not in dupdrop,
}
print(f"{'definition':28s} {'wrong':>6s} {'exact':>6s}  diff histogram (reported - actual)")
for name,f in defs.items():
    c=collections.Counter(x["project_id"] for x in L if x["project_id"] and f(x))
    diffs=[p["total_listings"]-c.get(p["project_id"],0) for p in P]
    h=collections.Counter(diffs)
    top=sorted(h.items(), key=lambda kv:-kv[1])[:7]
    print(f"{name:28s} {sum(1 for d in diffs if d):6d} {h[0]:6d}  {top}")
print("\ntotal listings with a project_id:", sum(1 for x in L if x["project_id"]))
print("sum(total_listings):", sum(p["total_listings"] for p in P))
print("projects referenced by listings:", len({x['project_id'] for x in L if x['project_id']}), "of", len(P))
print("\n-- sample projects: reported vs counts --")
call=collections.Counter(x["project_id"] for x in L if x["project_id"])
clive=collections.Counter(x["project_id"] for x in L if x["project_id"] and x["is_live"])
for p in P[:12]:
    print(f"  {p['project_id']} reported={p['total_listings']:3d} all={call.get(p['project_id'],0):3d} live={clive.get(p['project_id'],0):3d}")
