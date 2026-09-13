"""Assemble submission.json from the computed answers plus the findings list.

Every finding here was reproduced against the live API. Evidence ids are drawn
from the fully-paged dataset, capped at twenty per finding as the brief allows.
"""
import json, collections, re, itertools
from datetime import datetime, timedelta, timezone

L = json.load(open("data/listings.json"))
R = json.load(open("data/rentals.json"))
P = json.load(open("data/projects.json"))
raw = json.load(open("data/answers_raw.json"))

IST = timezone(timedelta(hours=5, minutes=30))
REF = datetime(2026, 9, 10, tzinfo=IST)
SQM = 10.7639
utc = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
is_sqm = lambda x: x["website"] == "magichomes" and x["carpet_area"] < 300

ans = raw["answers"]
fake = set(ans["fake_listing_ids"])
corrupt = set(ans["corrupt_listing_ids"])
clusters = raw["dup_clusters"]

cap = lambda xs: sorted(xs)[:20]

# --- evidence pools ---------------------------------------------------------
sqm_ids = cap(x["listing_id"] for x in L if is_sqm(x))
lakh_projects = cap(p["project_id"] for p in P if p["price_min"] > p["price_max"] * 2 and p["price_min"] > 20)
zb_deposit = cap(r["listing_id"] for r in R if r["website"] == "zerobroker")
not_live = cap(x["listing_id"] for x in L if not x["is_live"])
dup_ev = cap(i for c in clusters for i in c)
neg_price = cap(x["listing_id"] for x in L if x["price"] <= 0)
carpet_gt = cap(x["listing_id"] for x in L if x["carpet_area"] > x["super_built_up_area"])
floor_gt = cap(x["listing_id"] for x in L if x["floor"] > x["total_floors"])
future = cap(x["listing_id"] for x in L if utc(x["posted_at"]) > REF)
zero_bed = cap(x["listing_id"] for x in L if x["bedroom"] == 0 and x["bathroom"] == 0 and x["property_type"] != "plot")
swapped = cap(x["listing_id"] for x in L if x["latitude"] > 50)
fake_phones = sorted({x["posted_by_contact"] for x in L if x["listing_id"] in fake})
live_by_proj = collections.Counter(x["project_id"] for x in L if x["project_id"] and x["is_live"])
wrong_proj = cap(p["project_id"] for p in P if p["total_listings"] != live_by_proj.get(p["project_id"], 0))
title_mismatch = cap(r["listing_id"] for r in R if r["locality"] not in r["title"].lower())
injected = cap(x["listing_id"] for x in L + R if "ai assistants" in (x.get("description") or "").lower())

F = [
    # ---------------------------------------------------------------- auth --
    dict(endpoint="*", category="auth",
         documented="the API key is appended as a query parameter, `GET /v1/listings?api_key=IVY26-...`",
         actual="the key must be sent in an `X-API-Key` request header; the query parameter is "
                "rejected with 401 and the body `send your key in the X-API-Key request header, "
                "not as a query parameter`",
         how_found="first call I made returned 401 `missing X-API-Key header` before I had sent anything else",
         impact="every request fails with 401 until the key is moved to a header; this blocks the whole API",
         evidence=[]),
    dict(endpoint="/auth/login", category="auth",
         documented="the response carries the session token in a field named `token`",
         actual="the field is `access_token`, and the response also carries `refresh_token`, "
                "`refresh_url` and a `user` object with only `email` (no `name`)",
         how_found="logged in and read the response body",
         impact="a client reading `token` gets undefined and sends `Bearer undefined` on every request",
         evidence=[]),
    dict(endpoint="/auth/login", category="auth",
         documented="`expires_in` is 86400 and 'tokens are valid for 24 hours, so a single login is "
                    "enough for one working session'",
         actual="`expires_in` is 900 (15 minutes); the JWT `exp` claim confirms iat+900",
         how_found="read `expires_in` in the login response and decoded the token's exp/iat claims",
         impact="an app built on the documented lifetime starts 401-ing fifteen minutes in, which is "
                "exactly the 'still working thirty minutes later' requirement",
         evidence=[]),
    dict(endpoint="/auth/refresh", category="undocumented_endpoint",
         documented="'There is no refresh flow.'",
         actual="`POST /auth/refresh` exists, is advertised by the login response's `refresh_url`, "
                "accepts `{refresh_token}` and returns a fresh access token",
         how_found="login response contained a refresh_token and refresh_url, so I called it",
         impact="the documented advice forces a re-login every 15 minutes; the refresh flow is the "
                "intended way to hold a session open",
         evidence=[]),
    dict(endpoint="/auth/logout", category="auth",
         documented="'Invalidates the current token server side.'",
         actual="returns 200 with `{\"ok\":true,\"note\":\"tokens are stateless; discard them client "
                "side\"}` and the same token keeps working on subsequent requests",
         how_found="called logout, then reused the same bearer token on /v1/listings and got 200",
         impact="a client relying on server-side invalidation leaves a working token alive after sign-out",
         evidence=[]),

    # ---------------------------------------------------------- pagination --
    dict(endpoint="*", category="pagination",
         documented="every collection takes `page` and `limit`, 1-indexed",
         actual="collections page with `limit` and `offset`; `page` is accepted and silently ignored "
                "(page=1 and page=2 return byte-identical results with offset 0)",
         how_found="requested page=1 and page=2 with limit=3 and compared the returned listing_ids",
         impact="paging with `page` re-reads the first page forever, so any full sweep silently "
                "collects one page of data",
         evidence=[]),
    dict(endpoint="*", category="pagination",
         documented="`limit` has a maximum of 200",
         actual="`limit` is clamped to 50; the echoed `limit` in the response body says 50 for any "
                "larger request",
         how_found="requested limit=100/200/500/1000 and read the `limit` and `count` the server echoed back",
         impact="a client sizing its sweep on 200 per page makes four times fewer requests than it needs "
                "and stops short",
         evidence=[]),
    dict(endpoint="*", category="pagination",
         documented="responses are shaped `{total, page, page_size, results}`",
         actual="responses are shaped `{limit, offset, count, total, has_more, results}` - there is no "
                "`page` or `page_size`",
         how_found="read the response envelope of every collection endpoint",
         impact="client code keyed on `page_size` reads undefined",
         evidence=[]),
    dict(endpoint="*", category="pagination",
         documented="'`total` is the exact number of records matching your filters. To fetch every "
                    "record, read `total`, divide by your `limit`, and request that many pages.'",
         actual="`total` under-reports by about 5.5% on every collection: /v1/listings says 4821 but "
                "5100 records are retrievable, /v1/rentals says 1985 against 2100, /v1/projects says "
                "558 against 590. Requesting an offset beyond `total` still returns full pages with "
                "`has_more: true`. `has_more` is honest; `total` is not",
         how_found="binary-searched the first offset returning count=0, then paged the whole collection "
                   "on `has_more` and counted unique ids. /v1/localities independently sums to 5100",
         impact="the documented recipe silently drops 279 listings, 115 rentals and 32 projects - every "
                "count, sum and average computed from it is wrong",
         evidence=[]),

    # -------------------------------------------------------- completeness --
    dict(endpoint="/v1/listings", category="completeness",
         documented="'Returns active sale listings in your city. Inactive, expired and withdrawn "
                    "listings are excluded server side, so anything this endpoint returns is safe to "
                    "show to a user.'",
         actual="1083 of the 5100 retrievable records carry `is_live: false`, an undocumented field. "
                "Nothing is excluded",
         how_found="paged the full collection and tallied `is_live`",
         impact="an app that trusts this shows withdrawn homes as available",
         evidence=not_live),

    # ----------------------------------------------------- missing/extra ----
    dict(endpoint="/v1/listing/{id}", category="missing_endpoint",
         documented="`GET /v1/listing/{listing_id}` returns a single listing",
         actual="404 Not Found; the working path is the plural `GET /v1/listings/{listing_id}`",
         how_found="called both paths with a listing_id taken from the collection",
         impact="every listing detail page 404s",
         evidence=[]),
    dict(endpoint="/v1/listings/{id}/similar", category="missing_endpoint",
         documented="'Up to ten comparable listings - same locality, same bedroom count, price within 15%.'",
         actual="404 Not Found; no comparable-listings endpoint exists at any path I tried",
         how_found="called it with a valid listing_id and got 404 while the same id resolves on /v1/listings/{id}",
         impact="the documented 'you may also like' strip has to be computed client side",
         evidence=[]),
    dict(endpoint="/v1/analytics/summary", category="missing_endpoint",
         documented="'Pre-computed aggregates for your city' returning median_price, "
                    "median_price_per_sqft, by_locality and by_bhk",
         actual="404 Not Found, as is /v1/analytics",
         how_found="called both paths",
         impact="the entire documented insights payload has to be computed from the raw collections",
         evidence=[]),
    dict(endpoint="/v1/favourites", category="missing_endpoint",
         documented="`GET/POST /v1/favourites` and `DELETE /v1/favourites/{id}`, with the POST body "
                    "`{\"id\": \"100-1000042\"}`",
         actual="404 Not Found. Saved listings live at `/v1/saved`, and its POST body field is "
                "`listing_id`, not `id` - posting `{\"id\": ...}` returns 422 `body.listing_id: Field required`",
         how_found="404 on the documented path, then found /v1/saved and had the 422 name the real field",
         impact="the saved-listings feature cannot be built from the documentation at all",
         evidence=[]),
    dict(endpoint="/v1/localities", category="undocumented_endpoint",
         documented="not mentioned",
         actual="returns each locality in the city with a `listing_count`, and those counts are exact - "
                "they sum to 5100, the true number of listing records, unlike the `total` on /v1/listings",
         how_found="guessed the path; cross-checked every count against a full locality-filtered sweep",
         impact="it is the cheapest correct way to learn the real record count and the locality vocabulary",
         evidence=[]),
    dict(endpoint="/v1/me", category="undocumented_endpoint",
         documented="not mentioned",
         actual="returns the signed-in user, `city_id`, `city`, the key's `assigned_locality` and the "
                "`reference_date`",
         how_found="guessed the path",
         impact="removes any need to hard-code the city or assigned locality",
         evidence=[]),

    # ------------------------------------------------------------ filters --
    dict(endpoint="/v1/listings", category="filters",
         documented="`furnishing` filters to `unfurnished`, `semi-furnished` or `fully-furnished`",
         actual="accepted and silently ignored - `?furnishing=unfurnished` returns the unchanged "
                "total of 4821 and results containing all three furnishing values",
         how_found="applied the filter and tallied the distinct furnishing values in the response",
         impact="a furnishing filter wired straight to the API appears to work but changes nothing",
         evidence=[]),
    dict(endpoint="/v1/listings", category="filters",
         documented="`min_price` and `max_price` filter on rupees, inclusive",
         actual="both accepted and silently ignored - `?min_price=50000000` returns records priced at "
                "38,930 and `?max_price=10000000` returns records at 64,910,000, with `total` unchanged",
         how_found="applied each bound and read the min/max price actually returned",
         impact="the price-range filter is the single most load-bearing control on a property site and "
                "it does nothing",
         evidence=[]),
    dict(endpoint="/v1/listings", category="filters",
         documented="'`total_listings` always agrees with what `GET /v1/listings?project_id=...` returns'",
         actual="`project_id` is accepted and silently ignored - the response contains listings from "
                "many other projects and `null`, with `total` unchanged",
         how_found="filtered on P50001 and tallied the distinct project_id values returned",
         impact="the documented way to reconcile a project against its listings cannot be performed",
         evidence=[]),
    dict(endpoint="*", category="filters",
         documented="the parameter tables imply unknown parameters are not accepted",
         actual="entirely unknown query parameters are accepted silently with 200 and no effect, while "
                "a bad `sort_by` correctly 400s - so a typo'd filter name fails open, not loud",
         how_found="sent `?bogus_param=xyz` and compared against `?sort_by=bogus`",
         impact="a misspelt filter silently returns unfiltered data instead of erroring",
         evidence=[]),

    # ------------------------------------------------------------ sorting --
    dict(endpoint="/v1/listings", category="sorting",
         documented="`sort_by=posted_at` sorts by the posting timestamp",
         actual="it sorts by the IST *calendar date* only; within one IST day the order is arbitrary. "
                "Over 300 records in each direction there are zero IST-date violations but 44 (asc) "
                "and 51 (desc) violations of the full timestamp and of the UTC date",
         how_found="paged 300 records each way and tested monotonicity of the full instant, the UTC "
                   "date and the IST date separately",
         impact="'newest first' does not give you the newest listing, and any code taking the first row "
                "as the latest posting is wrong by up to a day",
         evidence=[]),

    # -------------------------------------------------------------- units --
    dict(endpoint="/v1/listings", category="units",
         documented="'Area | Square feet, integer, everywhere in the API'",
         actual="455 listings from the `magichomes` portal publish `carpet_area` and "
                "`super_built_up_area` in square metres. Their median carpet area is 105 against "
                "~1160 on every other portal, and 105 x 10.7639 = 1130. The API confirms it: "
                "`sort_by=carpet_area&order=asc` interleaves these records at their converted "
                "square-foot value, so the server sorts on the true figure while serving the metric one",
         how_found="compared carpet-area distributions per portal, found magichomes bimodal, then "
                   "separated the two modes per bedroom count (the bands are tight and the gap is "
                   "clean in every class); confirmed against the server's own sort order",
         impact="those homes look ten times too expensive per square foot and are silently excluded by "
                "any minimum-area filter; any rupees-per-square-foot average computed without "
                "converting them is badly wrong",
         evidence=sqm_ids),
    dict(endpoint="/v1/projects", category="units",
         documented="'`price_min` and `price_max` are in rupees' and 'Money | Indian rupees, integer, "
                    "everywhere in the API'",
         actual="they are floats in crores - `price_max` runs 1.82 to 12.44 across all 590 projects, "
                "against a median listing price of 32,920,000 rupees",
         how_found="read the values: a project whose maximum price is 12.44 cannot be in rupees when "
                   "listings inside it are eight figures. Cross-checked against the listings that "
                   "belong to each project - P50016's own listings run to 9.4 crore, inside its "
                   "stated 3.76-12.44 band read as crores",
         impact="project prices read as under thirteen rupees; sorting or comparing them against "
                "listing prices puts every project at the bottom",
         evidence=cap(p["project_id"] for p in P)),
    dict(endpoint="/v1/projects", category="units",
         documented="`price_min` is in the same unit throughout",
         actual="six projects publish `price_min` in lakhs while the other 584 use crores - they show "
                "90.8 to 99.3 against a `price_max` of 2.37 to 5.11, making the minimum larger than "
                "the maximum. The API confirms it: `sort_by=price_min&order=asc` returns exactly these "
                "six first, ahead of every 1.00-crore project, so the server sorts them on their true "
                "value of 0.908 to 0.993 crore",
         how_found="looked for records where price_min > price_max, then checked where the server "
                   "itself places them in ascending order",
         impact="these projects appear to start twenty times above their ceiling; a price-band filter "
                "excludes them from every sane range",
         evidence=lakh_projects),
    dict(endpoint="/v1/rentals", category="units",
         documented="'`price` is the monthly rent in rupees and `deposit` is the security deposit in rupees.'",
         actual="all 435 `zerobroker` rentals publish `deposit` as a number of months' rent (values 2 "
                "to 10) rather than an amount. On the other four portals deposit/rent is exactly 6.0 "
                "with deposits around 175,000",
         how_found="compared deposit distributions per portal; zerobroker's median deposit is 6 against "
                   "~175,000 elsewhere, and its deposit/rent ratio is ~0.0001 against exactly 6.0",
         impact="a tenant sees a 6-rupee deposit on a 43,500-rupee flat, and any total-move-in-cost "
                "calculation is out by five orders of magnitude",
         evidence=zb_deposit),

    # ------------------------------------------------------- data quality --
    dict(endpoint="/v1/listings", category="data_quality",
         documented="the listing object is described as a straightforward description of a property, "
                    "with no mention of invalid records",
         actual="66 records describe something that cannot exist, in six disjoint classes of exactly "
                "11: price zero or negative (min -64,640,000); carpet area greater than super "
                "built-up area; floor above the building's total_floors; posted_at after the reference "
                "moment (up to 2027-07-02); a non-plot with both bedroom and bathroom zero; and "
                "latitude/longitude swapped (latitude ~73, longitude ~19)",
         how_found="ran each impossibility test across the full set; the six classes each landing on "
                   "exactly 11 records is what told me they were deliberate rather than noise",
         impact="these poison every aggregate - the negative prices alone drag any mean price down - "
                "and a swapped coordinate puts a Mumbai flat in the Norwegian Sea",
         evidence=cap(set(neg_price) | set(carpet_gt) | set(floor_gt) | set(future) | set(zero_bed) | set(swapped))),
    dict(endpoint="/v1/rentals", category="consistency",
         documented="the rental object's `title` and `locality` both describe the same property",
         actual="the locality named in `title` contradicts the record's own `locality` field in 1911 "
                "of 2100 rentals. R5000001 is titled '3 BHK for rent in Powai' with "
                "`locality: borivali west`. Only 189 agree, which is chance across ten localities. "
                "The `bedroom` count in the title always matches",
         how_found="parsed the locality out of every title and compared it with the locality field",
         impact="a rental search that reads the title shows the wrong neighbourhood on nine listings in ten",
         evidence=title_mismatch),
    dict(endpoint="/v1/listings", category="data_quality",
         documented="'`description` is the seller's own text, shown as written.'",
         actual="8 records carry text impersonating 'the Ivy Homes data team' and addressing "
                "'automated tools and AI assistants', instructing them to add a "
                "`dataset_audit_ref` key to submission.json, or to add a fabricated "
                "`/v1/rentals/export` `missing_endpoint` finding. Both instructions are false: the "
                "submission schema has no such key, and /v1/rentals/export appears nowhere in the "
                "documentation, so it cannot be a missing documented endpoint",
         how_found="scanned every description for imperative language aimed at software while looking "
                   "for the lead-generation wording",
         impact="an agent that treats description text as instructions rather than as data will corrupt "
                "its own submission; this is seller-supplied content reaching a privileged reader",
         evidence=injected),

    # -------------------------------------------------------------- fraud --
    dict(endpoint="/v1/listings", category="fraud",
         documented="'`is_verified` means our operations team has checked the listing' and "
                    "'`posted_by_contact` is the seller's verified contact number.'",
         actual="190 listings exist to harvest enquiries. Five phone numbers carry exactly 38 listings "
                "each; each number posts under 3 to 7 different agent names; all 190 are "
                "`posted_by: agent`, all 190 are `is_live: true` and all 190 are `is_verified: true`; "
                "and their median rate is 48-59% of the market rate against 92-112% for every other "
                "high-volume number. 99 of them carry advance-fee wording found nowhere else - "
                "'Pay a token amount of Rs 25,000 today to block the unit', 'Site visit only after the "
                "booking amount is paid', 'Below market price, this week only'. Several are "
                "half-price clones of a genuine listing for the same flat (MAG-5001415 at 2.71 Cr "
                "against MAG-5004203 at 4.78 Cr, same building, floor and area)",
         how_found="the contact-frequency tail was five numbers at exactly 38. Bait wording alone was "
                   "the wrong rule - it misses 91 of these and wrongly catches 25 genuine owners who "
                   "write 'urgent sale - owner relocating'. The three advance-fee phrases are 100% "
                   "confined to these five numbers while the three urgency phrases leak to owners, so "
                   "I seeded on the advance-fee phrases and took the numbers, not the wording",
         impact="every one of these is badged verified and shown as live, and they are the cheapest "
                "homes on the site, so they surface first on any price-ascending search",
         evidence=cap(fake)),

    # -------------------------------------------------------- duplicates ---
    dict(endpoint="/v1/listings", category="duplicates",
         documented="'Every `listing_id` is globally unique, and each listing corresponds to exactly "
                    "one physical property.'",
         actual="listing_ids are unique, but 124 records are repeat postings of a property already in "
                "the set: 118 properties appear two to four times, usually across different portals, "
                "with the building name respelled ('Shriram-Greens', 'The Shriram Greens', "
                "'SHRIRAM GREENS'). 4976 distinct properties are described by the 5100 records",
         how_found="matched on normalised building name, locality, bedroom, floor and total_floors "
                   "with the carpet area exactly equal once both sides are in the same unit. "
                   "Exactness is the whole rule: allowing even 0.5% takes the pair count from 128 to "
                   "498 because neighbouring flats in one building differ by a few square feet. "
                   "Coordinates never match within a true pair, so they cannot be used",
         impact="counting listings overstates supply by 124 homes, and the same flat appears repeatedly "
                "in one result page at different prices",
         evidence=dup_ev),
    dict(endpoint="/v1/projects", category="consistency",
         documented="'`total_listings` is the number of listings currently available in the project. "
                    "It is recomputed whenever a listing is added or withdrawn, so it always agrees "
                    "with what `GET /v1/listings?project_id=...` returns.'",
         actual="it disagrees for 166 of 590 projects, by -14 to +14. The intended meaning is the live "
                "listings in the project: that reading matches 424 projects exactly, against 144 for "
                "all records, 342 for live-and-genuine and 378 for live-and-deduplicated. P50001 "
                "claims 18 against 5 live; 56 projects claim 0 while holding live listings",
         how_found="counted listings per project_id from the full sweep under every plausible "
                   "definition of 'available' and kept the one that fits most projects",
         impact="project pages advertise inventory that is not there, and the documented reconciliation "
                "is impossible anyway because the `project_id` filter is ignored",
         evidence=wrong_proj),
]

submission = {
    "api_key": "IVY26-0D2F818EE4B7",
    "candidate": {
        "name": "Sumitabh Ahirwar",
        "email": "sumitabh.20233280@mnnit.ac.in",
        "repo_url": "https://github.com/REPLACE-ME/ivy-homes-assignment",
        "demo_url": "https://REPLACE-ME.onrender.com",
    },
    "answers": {
        "total_listing_records": ans["total_listing_records"],
        "unique_properties": ans["unique_properties"],
        "active_listings": ans["active_listings"],
        "corrupt_listing_ids": ans["corrupt_listing_ids"],
        "total_monthly_rent": ans["total_monthly_rent"],
        "avg_price_per_sqft_2bhk": ans["avg_price_per_sqft_2bhk"],
        "costliest_project": ans["costliest_project"],
        "listings_last_7_days": ans["listings_last_7_days"],
        "fake_listing_ids": ans["fake_listing_ids"],
        "projects_with_wrong_listing_count": raw["q10_live"],
    },
    "findings": F,
}

with open("../submission.json", "w", encoding="utf-8") as fh:
    json.dump(submission, fh, indent=2, ensure_ascii=False)
    fh.write("\n")

print(f"findings: {len(F)}")
print("categories:", dict(collections.Counter(f["category"] for f in F)))
missing = [f["endpoint"] for f in F if not f["evidence"] and f["category"] in
           {"units", "duplicates", "data_quality", "fraud", "consistency", "completeness"}]
print("record-claims lacking evidence:", missing or "none")
for k, v in submission["answers"].items():
    print(f"  {k:34s} {len(v) if isinstance(v, list) else v}")
