import json, collections
L = json.load(open("data/listings.json"))
M = [x for x in L if x["website"]=="magichomes"]
v = sorted(x["carpet_area"] for x in M)
print("magichomes carpet histogram (bins of 50 up to 500, then 200):")
bins = collections.Counter()
for c in v:
    b = (c//50)*50 if c < 500 else (c//200)*200
    bins[b]+=1
for k in sorted(bins): print(f"  {k:5d}: {bins[k]}")
print("\ncount <300:", sum(1 for c in v if c<300), " >=300:", sum(1 for c in v if c>=300))
low = [x for x in M if x["carpet_area"]<300]
hi  = [x for x in M if x["carpet_area"]>=300]
print("low: bedroom dist", collections.Counter(x["bedroom"] for x in low))
print("low: median carpet", sorted(x["carpet_area"] for x in low)[len(low)//2])
print("low: median carpet*10.7639 =", sorted(x["carpet_area"] for x in low)[len(low)//2]*10.7639)
print("hi : median carpet", sorted(x["carpet_area"] for x in hi)[len(hi)//2])
print("\nlow sample:")
for x in low[:5]:
    print(" ", x["listing_id"], x["bedroom"],"BHK carpet",x["carpet_area"],"super",x["super_built_up_area"],"price",x["price"], "|", x["description"][:80])
print("\n-- do other websites have low carpet? --")
for w in sorted({x["website"] for x in L}):
    print(w, sum(1 for x in L if x["website"]==w and x["carpet_area"]<300))
