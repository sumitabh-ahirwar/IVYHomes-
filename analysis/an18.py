import json, collections, re
L = json.load(open("data/listings.json"))
SQM=10.7639
def ca_ft(x):
    ca=x["carpet_area"]; return round(ca*SQM) if (x["website"]=="magichomes" and ca<300) else ca
def norm(n):
    n=n.lower().replace("-"," ").replace("_"," "); n=re.sub(r"[^a-z0-9 ]"," ",n)
    n=re.sub(r"\s+"," ",n).strip(); n=re.sub(r"^the ","",n)
    return re.sub(r" (apartments|apartment|apts)$","",n).strip()
for keyname, kf in [
  ("name+loc+bed+floor+carpet", lambda x:(norm(x["apartment_name"]),x["locality"],x["bedroom"],x["floor"],ca_ft(x))),
  ("name+loc+bed+floor+carpet+price", lambda x:(norm(x["apartment_name"]),x["locality"],x["bedroom"],x["floor"],ca_ft(x),x["price"])),
  ("name+loc+bed+floor+price", lambda x:(norm(x["apartment_name"]),x["locality"],x["bedroom"],x["floor"],x["price"])),
  ("coord+bed+floor", lambda x:(x["latitude"],x["longitude"],x["bedroom"],x["floor"])),
  ("coord+carpet", lambda x:(x["latitude"],x["longitude"],ca_ft(x))),
]:
    k = collections.Counter(kf(x) for x in L)
    print(f"{keyname:34s} groups>1={sum(1 for v in k.values() if v>1):5d} extra={sum(v-1 for v in k.values() if v>1):5d} sizes={dict(collections.Counter(k.values()))}")

print("\n-- inspect groups under name+loc+bed+floor+carpet --")
g=collections.defaultdict(list)
for x in L: g[(norm(x["apartment_name"]),x["locality"],x["bedroom"],x["floor"],ca_ft(x))].append(x)
dups=[v for v in g.values() if len(v)>1]
print("groups:",len(dups))
samesite=sum(1 for v in dups if len({y['website'] for y in v})<len(v))
print("groups where 2 records share a website:", samesite)
pd=[]
for v in dups:
    ps=[y["price"] for y in v]
    pd.append((max(ps)-min(ps))/max(max(ps),1))
pd.sort()
print("price-diff pct percentiles:", {p:round(pd[len(pd)*p//100],4) for p in (10,25,50,75,90,99)})
for v in dups[:6]:
    print()
    for y in v: print(f"  {y['listing_id']:14s} {y['website']:11s} {y['apartment_name']:30s} ca={ca_ft(y):5d} price={y['price']:10d} {y['posted_at']} live={y['is_live']} ph={y['posted_by_contact']}")
