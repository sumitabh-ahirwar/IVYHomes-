import json, collections, re
L=json.load(open("data/listings.json")); R=json.load(open("data/rentals.json")); P=json.load(open("data/projects.json"))
raw=json.load(open("data/answers_raw.json")); fake=set(raw["answers"]["fake_listing_ids"])
print("lowercase check (doc: locality, furnishing, property_type, project_status lowercase):")
for f,ds in [("locality",L),("furnishing",L),("property_type",L),("project_status",P)]:
    v={x[f] for x in ds if x.get(f)}
    print(f"  {f:15s} all lower: {all(s==s.lower() for s in v)}  sample={sorted(v)[:4]}")
print("  apartment_name all lower:", all(x['apartment_name']==x['apartment_name'].lower() for x in L),
      " -- variants per normalised name exist:", 275)
print("\nproject_id null count:", sum(1 for x in L if x["project_id"] is None), "of", len(L))
print("listings whose project_id is not in /v1/projects:",
      len({x['project_id'] for x in L if x['project_id']} - {p['project_id'] for p in P}))
print("\nis_verified on the 190 fake listings:", collections.Counter(x["is_verified"] for x in L if x["listing_id"] in fake))
print("is_verified overall:", collections.Counter(x["is_verified"] for x in L))
print("\nmoney integer? listing price:", collections.Counter(type(x['price']).__name__ for x in L),
      " project price_max:", collections.Counter(type(x['price_max']).__name__ for x in P))
print("rental deposit type:", collections.Counter(type(x['deposit']).__name__ for x in R))
print("\nfake phones and their identity counts:")
fp={x["posted_by_contact"] for x in L if x["listing_id"] in fake}
for ph in sorted(fp):
    ns={x["posted_by_name"] for x in L if x["posted_by_contact"]==ph}
    print(f"  {ph}: {len(ns)} names, {sum(1 for x in L if x['posted_by_contact']==ph)} listings -> {sorted(ns)}")
print("\nany contact shared between a listing and a rental?",
      len({x['posted_by_contact'] for x in L} & {x['posted_by_contact'] for x in R}))
print("\ninjection scan in descriptions:")
pat=re.compile(r"(ai assistant|automated tool|submission\.json|must include|ignore (the )?previous|data team)", re.I)
hits=[x for x in L+R if pat.search(x.get("description") or "")]
print("  listings/rentals with instruction-like text:", len(hits))
for x in hits: print(f"   {x['listing_id']}: {x['description'][:230]}")
