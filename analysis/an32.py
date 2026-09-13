import json, collections, itertools
L=json.load(open("data/listings.json")); P=json.load(open("data/projects.json"))
raw=json.load(open("data/answers_raw.json"))
fake=set(raw["answers"]["fake_listing_ids"]); corrupt=set(raw["answers"]["corrupt_listing_ids"])
dupdrop=set()
for c in raw["dup_clusters"]: dupdrop|=set(c[1:])
preds={"live":lambda x:x["is_live"], "verified":lambda x:x["is_verified"],
       "notfake":lambda x:x["listing_id"] not in fake, "notcorrupt":lambda x:x["listing_id"] not in corrupt,
       "dedup":lambda x:x["listing_id"] not in dupdrop}
best=[]
for k in range(len(preds)+1):
    for combo in itertools.combinations(preds,k):
        f=lambda x,c=combo: all(preds[p](x) for p in c)
        cnt=collections.Counter(x["project_id"] for x in L if x["project_id"] and f(x))
        exact=sum(1 for p in P if p["total_listings"]==cnt.get(p["project_id"],0))
        best.append((exact, combo))
best.sort(reverse=True)
for e,c in best[:8]: print(f"  exact={e:4d}/590  wrong={590-e:4d}  filters={c or ('none',)}")
# characterise the 166 mismatches under 'live'
cnt=collections.Counter(x["project_id"] for x in L if x["project_id"] and x["is_live"])
wrong=[p for p in P if p["total_listings"]!=cnt.get(p["project_id"],0)]
print(f"\nwrong under 'live': {len(wrong)}")
d=[p["total_listings"]-cnt.get(p["project_id"],0) for p in wrong]
print("diff sign:", collections.Counter("over" if x>0 else "under" for x in d))
print("abs diff:", sorted(collections.Counter(abs(x) for x in d).items()))
print("status of wrong:", collections.Counter(p["project_status"] for p in wrong))
print("status of all:  ", collections.Counter(p["project_status"] for p in P))
print("wrong with reported=0:", sum(1 for p in wrong if p["total_listings"]==0))
print("projects with reported=0:", sum(1 for p in P if p["total_listings"]==0))
print("\nsample wrong:", [(p["project_id"],p["total_listings"],cnt.get(p["project_id"],0)) for p in wrong[:12]])
