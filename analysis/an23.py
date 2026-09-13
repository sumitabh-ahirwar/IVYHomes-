import json, collections, re, itertools
L = json.load(open("data/listings.json"))
SQM=10.7639
def is_sqm(x): return x["website"]=="magichomes" and x["carpet_area"]<300
def ft(x,f): return x[f]*SQM if is_sqm(x) else float(x[f])
def norm(n):
    n=n.lower().replace("-"," ").replace("_"," "); n=re.sub(r"[^a-z0-9 ]"," ",n)
    n=re.sub(r"\s+"," ",n).strip(); n=re.sub(r"^the ","",n)
    return re.sub(r" (apartments|apartment|apts)$","",n).strip()
def close(a,b,f,tol): 
    A,B=ft(a,f),ft(b,f); return abs(A-B)/max(A,B)<=tol
def pairs(need_floor, area_tol, sbu_tol, need_name):
    blocks=collections.defaultdict(list)
    for x in L:
        k=(x["locality"],x["bedroom"],x["floor"]) if need_floor else (x["locality"],x["bedroom"])
        blocks[k].append(x)
    out=[]
    for b in blocks.values():
        for a,c in itertools.combinations(b,2):
            if need_name and norm(a["apartment_name"])!=norm(c["apartment_name"]): continue
            if not close(a,c,"carpet_area",area_tol): continue
            if sbu_tol is not None and not close(a,c,"super_built_up_area",sbu_tol): continue
            out.append((a,c))
    return out
for nf,at,st,nn,label in [
 (True,0.005,0.03,True,"floor=same area<=0.5% sbu<=3% name=yes"),
 (True,0.01, 0.03,True,"floor=same area<=1%   sbu<=3% name=yes"),
 (True,0.02, 0.05,True,"floor=same area<=2%   sbu<=5% name=yes"),
 (True,0.005,None,True,"floor=same area<=0.5% sbu=any name=yes"),
 (False,0.005,0.03,True,"floor=ANY  area<=0.5% sbu<=3% name=yes"),
 (True,0.005,0.03,False,"floor=same area<=0.5% sbu<=3% name=ANY"),
]:
    p=pairs(nf,at,st,nn)
    adj=collections.defaultdict(set)
    for a,c in p: adj[a["listing_id"]].add(c["listing_id"]); adj[c["listing_id"]].add(a["listing_id"])
    seen=set(); extra=0; ncl=0
    for n in adj:
        if n in seen: continue
        st_=[n]; comp=set()
        while st_:
            u=st_.pop()
            if u in comp: continue
            comp.add(u); seen.add(u); st_.extend(adj[u]-comp)
        ncl+=1; extra+=len(comp)-1
    print(f"{label:46s} pairs={len(p):5d} clusters={ncl:4d} extra={extra:4d} unique={5100-extra}")
