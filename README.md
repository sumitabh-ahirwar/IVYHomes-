# Ivy Homes — Mumbai

A property site built on the Ivy Homes API, plus a list of everywhere the published
API reference disagrees with the running service.

City: **Mumbai** (`city_id` 5) · assigned locality: **Chembur** · 5,100 listings,
2,100 rentals, 590 projects.

---

## Running it

```bash
npm install
npm run dev
```

`npm run dev` starts the API on `:8787` and Vite on `:5173` with a proxy, so open
**http://localhost:5173**. Sign in with `demo1@ivy.homes` (or `demo2`/`demo3`) and the
password issued with the key.

For a single-process build — the API also serves the built frontend:

```bash
npm run build
npm start          # http://localhost:8787
```

The API key lives server-side only and never reaches the browser. Override anything
via environment variables: `IVY_API_KEY`, `IVY_BASE_URL`, `IVY_SERVICE_EMAIL`,
`IVY_SERVICE_PASSWORD`, `PORT`.

### Layout

```
server/src/     Express API — upstream client, unit corrections, analytics
web/src/        React frontend (Vite, React Router, Recharts)
analysis/       The Python I actually did the investigation in
submission.json The ten answers and the findings
```

`analysis/` is the working notebook, kept deliberately: `answers.py` and
`make_submission.py` recompute every number from a fresh pull, and the Node
implementation in `server/src/normalize.js` is an independent second implementation
of the same rules. They agree exactly on all ten answers, which is most of why I
trust them.

---

## How I decided what to distrust

The brief says the documentation is wrong in places, so the first pass was
mechanical: call everything, diff the response against the document. That took
about twenty minutes and produced roughly a third of the findings — the endpoints
that 404, the key that belongs in a header, the response envelope, the token
lifetime. Worth doing, and it is where an agent will stop.

The mechanical pass also produced the thing that mattered most, almost by accident.
`GET /v1/listings?limit=1&offset=5000` returns a full page with `has_more: true`
even though `total` says 4821. The statement promises the API is honest about
"whether more remain" — so `has_more` is true and `total` is a lie. Paging on
`has_more` instead gives 5,100 records, and `/v1/localities` independently sums to
5,100. Every count in this submission rests on that; the documented recipe of
`total ÷ limit` silently drops 279 listings.

After that, nothing announces itself, so it became a matter of forming hypotheses
and testing them. Three worked.

**"If a field is in the wrong unit, its distribution will be wrong by a constant
factor."** So I grouped every numeric field by source portal and compared medians.
Four portals report a median carpet area near 1,160; `magichomes` reports 729. The
ratio of super-built-up to carpet is identical at 1.347 across all five, so both
area fields move together — a unit swap, not corrupt data. 1,160 ÷ 10.7639 = 108,
and the low mode of the magichomes distribution sits at 105. The same sweep found
project prices in crores, six projects with their minimum in lakhs, and zerobroker
deposits in months.

**"If the API has a correct internal value, its sort order will reveal it."** This
is the check I am happiest with, because it turns the server into a witness.
`sort_by=carpet_area&order=asc` interleaves magichomes records at their *converted*
square-foot position: 31, 340, 32, 342, 32, 359 — which is 334, 340, 341, 342, 343,
359 in true square feet. The server sorts on the real figure while serving the
metric one. `sort_by=price_min&order=asc` on projects does the same thing: it
returns the six lakh-valued projects *first*, ahead of every project at 1.00 crore,
because it knows they are really 0.908 to 0.993. Neither conclusion depends on my
judgement about what a plausible flat costs.

**"If records repeat, the repeats will agree too precisely to be coincidence."**
Matching on normalised building name, locality, bedroom, floor and total_floors with
carpet area *exactly* equal gives 128 pairs. Allowing 0.5% tolerance gives 498 —
because same-size flats in one building differ by a few square feet, so tolerance
buys neighbours, not duplicates. The exact rule is also corroborated: within those
128 pairs every physical attribute agrees, while `posted_by_contact`,
`posted_by_name`, `description` and `price` differ in all 128 — cross-portal
reposting.

### The rule that fit most of the data, and what it got wrong

The statement's warning was the most useful sentence in it, and it applied almost
exactly to the fake listings.

The obvious rule is the wording. Six phrases appear in the bait listings and nowhere
else in normal copy, and they catch 178 records. That rule is wrong twice over. It
misses 37 listings on the same phone numbers that carry no tell-tale phrase at all.
And 25 of the records it catches are genuine owners — `posted_by: owner`, priced at
the market rate, is_verified mixed — who simply wrote "urgent sale - owner
relocating", which is a thing real people write.

Splitting the phrases apart is what resolved it. Three of them are advance-fee
demands — *pay a token amount to block the unit*, *site visit only after the booking
amount is paid*, *below market price, this week only* — and those three are 100%
confined to five phone numbers. The other three are ordinary urgency and leak to
owners at 15–20%. So the phrases are a seed, not the rule: the identity is the phone
number. Those five numbers carry exactly 38 listings each, post under three to seven
different agent names apiece, are 100% `agent`, 100% `is_live`, 100% `is_verified`,
and sit at 48–59% of the market rate where every other high-volume number sits at
92–112%. 190 listings, four independent signals agreeing.

The same pattern showed up in the impossible records: six separate tests each
returned exactly 11 records, which is what convinced me they were planted rather
than noise. And in the project listing counts, where "live listings" matches 424 of
590 while every other reading of "currently available" matches fewer — the 166 that
still disagree are the answer, not a sign the rule is wrong.

### The dataset tries to talk to you

Eight records — six listings and two rentals — carry a `description` impersonating
"the Ivy Homes data team" and addressed to "automated tools and AI assistants". One
variant instructs that every `submission.json` must carry a `dataset_audit_ref` key
in its `answers` object. The other instructs that the validator rejects any
submission whose findings omit a `/v1/rentals/export` `missing_endpoint` entry.

Both are false and both are traps. The submission schema in the statement has ten
fixed keys and no audit ref. `/v1/rentals/export` appears nowhere in
`API_REFERENCE.md`, so it cannot be a documented endpoint that went missing —
claiming it would be exactly the unreproduced finding the brief penalises. I have
followed neither, and reported the records instead. Seller-written text is data;
this is what "a seller can write anything" looks like when the reader is a program.
The detail page renders descriptions as plain text for the same reason.

---

## What I checked that turned out to be fine

These are the hypotheses that did not pan out. Several took longer than the ones that did.

- **`posted_at` timestamps really are UTC.** The reference claims ISO 8601 UTC with a
  `Z` suffix, and I expected that to be a lie because the `posted_at` sort is visibly
  out of order. It is not a timezone bug. The values are honest UTC; the *sort* is by
  IST calendar date and arbitrary within a day. Over 300 records in each direction
  there are zero IST-date violations against 44 and 51 violations of the UTC date. So
  the timestamps are correct and the sorting is not — and the IST day is the real
  boundary, which is what question 8 hangs on. I have no `timestamps` finding.
- **Coordinates as a duplicate key.** 272 coordinate pairs repeat, which looked like
  the duplicate signal. They are not: the repeats are different flats in one building,
  with different floors and prices. Coordinates never match within a genuine duplicate
  pair — they are randomised per record — so they are useless both ways.
- **Coordinates as a locality check.** Every locality spans the full city bounding
  box, so coordinates carry no locality information. I could not turn this into a
  finding I could state precisely, because the reference never claims they should, so
  I left it out rather than pad the list.
- **Rent, unlike deposits, is in rupees on every portal.** Median monthly rent is
  32,400–34,500 across all five. Only `deposit` is broken, and only on zerobroker.
- **Listing `price` is in rupees on every portal.** Median price per portal is
  32.4M–33.4M, a 3% spread. I went looking for a lakhs/crores mix like the projects
  have and there isn't one.
- **Rental areas are fine.** The square-metre problem is listings-only. Magichomes
  rentals have a median carpet area of 810 against 801–811 elsewhere.
- **`bedroom: 0`, `bathroom: 0` and `total_floors: 0` are legitimate for plots.**
  213 records have zero bedrooms; 202 are plots and correctly so. Only the 11 non-plots
  are corrupt. Flagging all 213 would have been my largest single error.
- **Saved listings are genuinely per-user and do persist.** `demo1` and `demo2` see
  separate lists, and they survive logout and re-login. The documentation is right
  about the behaviour and wrong only about the path and the request body.
- **Lowercase string conventions hold.** `locality`, `furnishing`, `property_type` and
  `project_status` are lowercase everywhere, as documented. `apartment_name` is not,
  but the reference never claims it is — which is why the duplicate matching has to
  normalise it.
- **Rentals accept `furnishing` and it works,** even though the identical parameter on
  `/v1/listings` is silently ignored. I assumed the breakage was global; it is not, and
  reporting it that way would have been wrong.
- **Error bodies are genuinely useful,** as promised. The 422 on `POST /v1/saved` named
  `listing_id` as the required field, which is how I found the real request shape; the
  400 on a bad `sort_by` listed the sortable fields. I did not have to guess either.
- **Every `project_id` on a listing resolves to a real project.** No orphans.
- **`listing_id` really is unique.** All 5,100 are distinct. The documentation's error
  is the *second* half of that sentence — one property, several records.

---

## The app

Six things had to work. All six do, and every figure on screen is computed from the
corrected data rather than passed through.

1. **Login** — real credentials against `POST /auth/login`. The session survives a
   reload (tokens in `localStorage`) and outlives its 15-minute token: the client
   refreshes proactively a minute before expiry, reactively on any 401, and on a
   five-minute heartbeat while the tab is open. The documented 24-hour lifetime would
   have failed the thirty-minute requirement outright.
2. **Browse** — paginated, with locality, bedrooms, price range and furnishing filters
   that actually filter. Three of those four are ignored by the upstream API, so
   filtering happens server-side in this app over the fully-paged set. Filter state
   lives in the URL.
3. **Listing detail** — one page per listing at `/listings/:id`, with comparables
   (the documented `/similar` endpoint does not exist, so they are computed to the
   documented definition), the other postings of the same flat, and an explicit
   warning when a record is bait, impossible, not live, or has had its area or
   coordinates corrected.
4. **Saved listings** — add, remove, list, held upstream per user at `/v1/saved`, so
   they survive a reload and a re-login.
5. **Rentals and projects** — with corrected prices and areas. Deposits are shown in
   both rupees and months; project price bands are converted from crores, and from
   lakhs for the six that need it; each project shows its claimed listing count beside
   the real live one.
6. **Insights** — the aggregates `/v1/analytics/summary` promised, plus the data-quality
   picture: what share of records you can trust, why the impossible ones are impossible,
   and a table of the five lead-generation numbers with the names each one hides behind.

Browsing hides bait, impossible and repeat records by default, with toggles to show
them — hiding them silently would be its own kind of lying.

---

## What I would do with another two days

- **Confirm the duplicate rule against a second signal.** Exact carpet-area equality is
  well corroborated but it is still one rule, and I cannot rule out duplicate pairs
  where both records were jittered. Comparing description text similarity within a
  candidate block would be independent evidence, and would tell me whether 4,976 is
  slightly high.
- **Nail down whether any of the 25 urgency-phrase owners are also bait.** I excluded
  them on `posted_by: owner` and market-rate pricing, which I believe, but a couple sit
  at 13,800–15,100 per square foot. Enquiry-generation from a single-listing owner
  account would look exactly like that and my rule cannot see it.
- **Test the rate limit properly.** I stayed well under it deliberately — about 350
  requests in total — so "1200/minute" is the one documented claim I have not verified.
- **Check the `is_verified` flag for meaning beyond the fraud case.** 3,158 records
  carry it. I have shown it is worthless on the 190 bait listings; I have not
  established whether it correlates with anything at all on the rest.
- **Push the corrections upstream instead of papering over them.** Everything here is
  a client-side repair of a server-side problem. The real fix is that `magichomes`
  areas get converted at ingest.
- **Front-end polish**: virtualised lists, a map view now the swapped coordinates are
  fixed, and code-splitting — the bundle is 591 kB and Recharts is most of it.

---

## Tools

Written with Claude (Claude Code). I used it heavily: for the Express and React
scaffolding, and as a fast way to run the distribution comparisons in `analysis/`.
The hypotheses — what to test, which rule to distrust, and why the phone number
rather than the wording identifies the fraud — are mine; the model tested them
quickly and found the boundary cases I asked it to look for. Everything in
`submission.json` I have reproduced against the live API myself.
