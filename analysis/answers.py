"""Compute the ten answers from the fully-paged dataset."""
import json, collections, re, itertools
from datetime import datetime, timedelta, timezone

L=json.load(open("data/listings.json")); R=json.load(open("data/rentals.json")); P=json.load(open("data/projects.json"))
IST=timezone(timedelta(hours=5,minutes=30)); REF=datetime(2026,9,10,0,0,0,tzinfo=IST); SQM=10.7639
def utc(s): return datetime.fromisoformat(s.replace("Z","+00:00"))
def is_sqm(x): return x["website"]=="magichomes" and x["carpet_area"]<300
def carpet_ft(x): return x["carpet_area"]*SQM if is_sqm(x) else float(x["carpet_area"])

# Q1
q1=len(L)

# Q4 corrupt: six disjoint impossibility classes
corrupt=set()
cls={
 "price<=0":        [x for x in L if x["price"]<=0],
 "carpet>super":    [x for x in L if x["carpet_area"]>x["super_built_up_area"]],
 "floor>total":     [x for x in L if x["floor"]>x["total_floors"]],
 "posted_future":   [x for x in L if utc(x["posted_at"])>REF],
 "0bed0bath_nonplot":[x for x in L if x["bedroom"]==0 and x["bathroom"]==0 and x["property_type"]!="plot"],
 "latlon_swapped":  [x for x in L if x["latitude"]>50],
}
for k,v in cls.items():
    corrupt |= {x["listing_id"] for x in v}
    print(f"  corrupt/{k:18s} {len(v)}")
q4=sorted(corrupt)

# Q9 fake: 5 lead-gen phone numbers
ADV=["site visit only after the booking amount is paid","below market price, this week only",
     "pay a token amount of rs 25,000 today to block the unit"]
fake_phones={x["posted_by_contact"] for x in L if any(p in x["description"].lower() for p in ADV)}
q9=sorted(x["listing_id"] for x in L if x["posted_by_contact"] in fake_phones)
print(f"  fake phones: {len(fake_phones)} -> {len(q9)} listings")

# Q2 unique properties
def norm(n):
    n=n.lower().replace("-"," ").replace("_"," "); n=re.sub(r"[^a-z0-9 ]"," ",n)
    n=re.sub(r"\s+"," ",n).strip(); n=re.sub(r"^the ","",n)
    return re.sub(r" (apartments|apartment|apts)$","",n).strip()
def area_eq(a,b):
    A,B=a["carpet_area"],b["carpet_area"]; sa,sb=is_sqm(a),is_sqm(b)
    if sa==sb: return A==B
    return (round(B/SQM)==A) if sa else (round(A/SQM)==B)
blocks=collections.defaultdict(list)
for x in L: blocks[(norm(x["apartment_name"]),x["locality"],x["bedroom"],x["floor"],x["total_floors"])].append(x)
adj=collections.defaultdict(set)
for b in blocks.values():
    for a,c in itertools.combinations(b,2):
        if area_eq(a,c):
            adj[a["listing_id"]].add(c["listing_id"]); adj[c["listing_id"]].add(a["listing_id"])
seen=set(); extra=0; clusters=[]
for n in adj:
    if n in seen: continue
    st=[n]; comp=set()
    while st:
        u=st.pop()
        if u in comp: continue
        comp.add(u); seen.add(u); st.extend(adj[u]-comp)
    clusters.append(sorted(comp)); extra+=len(comp)-1
q2=len(L)-extra
print(f"  dup clusters {len(clusters)}, redundant records {extra}")

# Q3
q3=sum(1 for x in L if x["is_live"])

# Q5 rent in assigned locality
q5=sum(x["price"] for x in R if x["locality"]=="chembur")
print(f"  chembur rentals: {sum(1 for x in R if x['locality']=='chembur')}")

# Q6
excl=set(q4)|set(q9)
sel=[x for x in L if x["is_live"] and x["bedroom"]==2 and x["listing_id"] not in excl]
q6=round(sum(x["price"]/carpet_ft(x) for x in sel)/len(sel),2)
print(f"  2BHK live minus excl: {len(sel)}")

# Q7 project price_max: crores -> INR
top=max(P,key=lambda x:x["price_max"])
q7={"project_id":top["project_id"],"price_max_inr":int(round(top["price_max"]*10_000_000))}

# Q8
q8=sum(1 for x in L if REF-timedelta(days=7) <= utc(x["posted_at"]).astimezone(IST) < REF)

# Q10
cnt=collections.Counter(x["project_id"] for x in L if x["project_id"])
cnt_live=collections.Counter(x["project_id"] for x in L if x["project_id"] and x["is_live"])
q10_all=sum(1 for p in P if p["total_listings"]!=cnt.get(p["project_id"],0))
q10_live=sum(1 for p in P if p["total_listings"]!=cnt_live.get(p["project_id"],0))
print(f"  wrong count: all-records={q10_all}  live-only={q10_live}  (of {len(P)})")

ans=dict(total_listing_records=q1, unique_properties=q2, active_listings=q3,
 corrupt_listing_ids=q4, total_monthly_rent=q5, avg_price_per_sqft_2bhk=q6,
 costliest_project=q7, listings_last_7_days=q8, projects_with_wrong_listing_count=None,
 fake_listing_ids=q9)
json.dump({"answers":ans,"q10_all":q10_all,"q10_live":q10_live,"dup_clusters":clusters},
          open("data/answers_raw.json","w"), indent=1)
print("\n== ANSWERS ==")
for k,v in ans.items():
    print(f"  {k:34s} {len(v) if isinstance(v,list) else v}" + (f"  (list of {len(v)})" if isinstance(v,list) else ""))
