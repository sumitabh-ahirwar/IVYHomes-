import json, collections, re
L = json.load(open("data/listings.json"))
FAKE5 = {'+912007133812','+912007145137','+912000039837','+912007219058','+912003561453'}
f5 = [x for x in L if x["posted_by_contact"] in FAKE5]
print("-- FAKE5 descriptions (10) --")
for x in f5[:10]: print(" ", x["listing_id"], "|", x["description"])
print("\n-- normal descriptions (6) --")
for x in L[:6]:
    if x["posted_by_contact"] not in FAKE5: print(" ", x["listing_id"], "|", x["description"])

print("\n-- description phrase frequency: FAKE5 vs rest --")
def toks(s): return set(re.findall(r"[a-z][a-z'\-]+", s.lower()))
fa = collections.Counter(); re_ = collections.Counter()
for x in L:
    (fa if x["posted_by_contact"] in FAKE5 else re_).update(toks(x["description"]))
nf, nr = len(f5), len(L)-len(f5)
rows=[]
for w,c in fa.items():
    pf, pr = c/nf, re_.get(w,0)/nr
    if pf > 0.05 and pf > pr*3: rows.append((pf/max(pr,1e-6), w, round(pf,3), round(pr,3)))
rows.sort(reverse=True)
for r in rows[:20]: print(f"   {r[1]:20s} fake={r[2]:.3f} rest={r[3]:.3f}")
print("\n-- words common in rest but rare in FAKE5 --")
rows=[]
for w,c in re_.items():
    pr, pf = c/nr, fa.get(w,0)/nf
    if pr > 0.05 and pr > pf*3: rows.append((pr/max(pf,1e-6), w, round(pr,3), round(pf,3)))
rows.sort(reverse=True)
for r in rows[:20]: print(f"   {r[1]:20s} rest={r[2]:.3f} fake={r[3]:.3f}")
