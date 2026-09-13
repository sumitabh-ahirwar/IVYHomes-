import json, collections
L = json.load(open("data/listings.json"))
SQM=10.7639
def ca_ft(x):
    ca=x["carpet_area"]; return ca*SQM if (x["website"]=="magichomes" and ca<300) else ca
def ppsf(x):
    c=ca_ft(x); return x["price"]/c if c>0 and x["price"]>0 else None
allp=sorted(v for v in (ppsf(x) for x in L) if v); MED=allp[len(allp)//2]
ADV = ["site visit only after the booking amount is paid","below market price, this week only",
       "pay a token amount of rs 25,000 today to block the unit"]
byphone = collections.defaultdict(list)
for x in L: byphone[x["posted_by_contact"]].append(x)
rows=[]
for ph, rs in byphone.items():
    p = sorted(v for v in (ppsf(x) for x in rs) if v)
    rows.append(dict(ph=ph, n=len(rs), names=len({x['posted_by_name'] for x in rs}),
      allagent=all(x['posted_by']=='agent' for x in rs), alllive=all(x['is_live'] for x in rs),
      allver=all(x['is_verified'] for x in rs), ratio=(p[len(p)//2]/MED) if p else 0,
      adv=sum(1 for x in rs if any(a in x['description'].lower() for a in ADV))))
rows.sort(key=lambda r:-r["n"])
print(f"{'phone':16s} {'n':>4s} {'#names':>6s} agent live ver  {'ppsfRatio':>9s} {'advFee':>6s}")
for r in rows[:16]:
    print(f"{r['ph']:16s} {r['n']:4d} {r['names']:6d}  {int(r['allagent'])}    {int(r['alllive'])}    {int(r['allver'])}   {r['ratio']:9.2f} {r['adv']:6d}")
print("\n-- phones with >=1 advance-fee phrase --")
adv_ph = {r['ph'] for r in rows if r['adv']>0}
print(len(adv_ph), sorted(adv_ph))
print("\n-- rule: multi-name AND all-agent AND all-live AND all-verified AND ratio<0.75 --")
sel=[r for r in rows if r['names']>1 and r['allagent'] and r['alllive'] and r['allver'] and r['ratio']<0.75]
print("phones:", len(sel), "listings:", sum(r['n'] for r in sel))
for r in sel: print("  ", r['ph'], r['n'], round(r['ratio'],2))
print("\n-- how many non-selected phones are all-live AND all-verified AND all-agent? --")
o=[r for r in rows if r['allagent'] and r['alllive'] and r['allver'] and r not in sel]
print(len(o), "phones,", sum(r['n'] for r in o), "listings; max n =", max((r['n'] for r in o), default=0),
      "; ppsf ratios:", sorted(round(r['ratio'],2) for r in o)[:12])
