import json, collections, re, itertools
L = json.load(open("data/listings.json"))
SQM=10.7639
def ca_ft(x):
    ca=x["carpet_area"]; return ca*SQM if (x["website"]=="magichomes" and ca<300) else float(ca)
def norm(n):
    n=n.lower().replace("-"," ").replace("_"," "); n=re.sub(r"[^a-z0-9 ]"," ",n)
    n=re.sub(r"\s+"," ",n).strip(); n=re.sub(r"^the ","",n)
    return re.sub(r" (apartments|apartment|apts)$","",n).strip()
# block by (name, locality, bedroom) then compare pairs with tolerances
blocks=collections.defaultdict(list)
for x in L: blocks[(norm(x["apartment_name"]),x["locality"],x["bedroom"])].append(x)
def count(tol_area, need_floor, tol_price):
    pairs=0
    for b in blocks.values():
        for a,c in itertools.combinations(b,2):
            if need_floor and a["floor"]!=c["floor"]: continue
            A,C=ca_ft(a),ca_ft(c)
            if abs(A-C)/max(A,C) > tol_area: continue
            if tol_price is not None:
                pa,pc=a["price"],c["price"]
                if abs(pa-pc)/max(abs(pa),abs(pc),1) > tol_price: continue
            pairs+=1
    return pairs
for tol in [0.0, 0.005, 0.01, 0.02, 0.05, 0.10]:
    print(f"area tol {tol*100:4.1f}% floor=same price=any -> pairs {count(tol, True, None)}")
print()
for tol in [0.0, 0.01, 0.02, 0.05]:
    print(f"area tol {tol*100:4.1f}% floor=ANY  price=any -> pairs {count(tol, False, None)}")
print()
print("exact area, same floor, price within 10%:", count(0.0, True, 0.10))
print("exact area, same floor, price within 60%:", count(0.0, True, 0.60))
