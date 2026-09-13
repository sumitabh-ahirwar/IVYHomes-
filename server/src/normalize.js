/**
 * Unit and integrity corrections applied to every record before it reaches the UI.
 *
 * Each rule below was derived from the data and then confirmed a second time by
 * the API's own sort behaviour: the server sorts on the *true* value, which is
 * how you can tell the displayed value is in the wrong unit.
 */

export const SQFT_PER_SQM = 10.7639;
export const RUPEES_PER_CRORE = 10_000_000;
export const RUPEES_PER_LAKH = 100_000;
export const REFERENCE = new Date("2026-09-10T00:00:00+05:30");
export const IST_OFFSET_MIN = 330;

/** Calendar date in IST, as YYYY-MM-DD. The API sorts `posted_at` by this. */
export function istDate(iso) {
  const d = new Date(iso);
  return new Date(d.getTime() + IST_OFFSET_MIN * 60_000).toISOString().slice(0, 10);
}

/* ------------------------------------------------------------------ areas -- */

/**
 * Learn the plausible carpet-area band (in sq ft) for each bedroom count from
 * the four portals known to publish square feet. Areas are tightly clustered
 * per bedroom count, which is what makes the square-metre records separable.
 */
export function learnAreaBands(listings) {
  const buckets = new Map();
  for (const x of listings) {
    if (x.website === "magichomes") continue; // the suspect portal
    if (!(x.carpet_area > 0)) continue;
    if (!buckets.has(x.bedroom)) buckets.set(x.bedroom, []);
    buckets.get(x.bedroom).push(x.carpet_area);
  }
  const bands = new Map();
  for (const [bhk, arr] of buckets) {
    arr.sort((a, b) => a - b);
    const at = (q) => arr[Math.min(arr.length - 1, Math.max(0, Math.floor(arr.length * q)))];
    bands.set(bhk, { lo: at(0.01), hi: at(0.99) });
  }
  return bands;
}

/**
 * True when this record's areas are published in square metres, not square feet.
 *
 * Decided per record: the value is metric when multiplying by 10.7639 lands it
 * inside its bedroom class's square-foot band and the raw value does not. A
 * fixed threshold would be wrong, because a 1 BHK at 400 sq ft and a 4 BHK at
 * 150 sq m overlap in raw magnitude.
 */
export function areaIsSqm(x, bands) {
  if (x.website !== "magichomes") return false;
  const band = bands.get(x.bedroom);
  const c = x.carpet_area;
  if (!band || !(c > 0)) return false;
  const inFeet = c >= band.lo * 0.8 && c <= band.hi * 1.25;
  const inMetres = c * SQFT_PER_SQM >= band.lo * 0.8 && c * SQFT_PER_SQM <= band.hi * 1.25;
  if (inMetres && !inFeet) return true;
  // Records corrupted another way (carpet above super built-up) sit in neither
  // band; for this portal the raw magnitude still settles it.
  if (!inMetres && !inFeet) return c < band.lo * 0.5;
  return false;
}

/* ------------------------------------------------- listing integrity flags -- */

/** Six disjoint classes of record describing something that cannot exist. */
export function corruptionReasons(x) {
  const why = [];
  if (x.price <= 0) why.push("price is zero or negative");
  if (x.carpet_area > x.super_built_up_area) why.push("carpet area exceeds super built-up area");
  if (x.floor > x.total_floors) why.push("floor is above the building's top floor");
  if (new Date(x.posted_at) > REFERENCE) why.push("posted in the future");
  if (x.bedroom === 0 && x.bathroom === 0 && x.property_type !== "plot") {
    why.push("a non-plot with no bedrooms and no bathrooms");
  }
  if (x.latitude > 50) why.push("latitude and longitude are swapped");
  return why;
}

/** Advance-fee wording that appears only on the lead-generation accounts. */
const ADVANCE_FEE = [
  "site visit only after the booking amount is paid",
  "below market price, this week only",
  "pay a token amount of rs 25,000 today to block the unit",
];

/**
 * Identify the lead-generation operation.
 *
 * The phone number is the identity, not the wording: a fifth of the bait
 * listings carry no tell-tale phrase, and genuine owners do write "urgent
 * sale". So we seed from the advance-fee phrases, then take every listing on
 * the numbers those phrases appear on.
 */
export function findFakePhones(listings) {
  const phones = new Set();
  for (const x of listings) {
    const d = (x.description || "").toLowerCase();
    if (ADVANCE_FEE.some((p) => d.includes(p))) phones.add(x.posted_by_contact);
  }
  return phones;
}

/* --------------------------------------------------------------- duplicates */

/** Collapse the spelling variants portals use for the same building. */
export function normaliseName(name) {
  return String(name || "")
    .toLowerCase()
    .replace(/[-_]/g, " ")
    .replace(/[^a-z0-9 ]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^the /, "")
    .replace(/ (apartments|apartment|apts)$/, "")
    .trim();
}

/** Area equality that respects each record's own unit granularity. */
function sameArea(a, b) {
  const A = a._raw_carpet;
  const B = b._raw_carpet;
  if (a._area_in_sqm === b._area_in_sqm) return A === B;
  return a._area_in_sqm
    ? Math.round(B / SQFT_PER_SQM) === A
    : Math.round(A / SQFT_PER_SQM) === B;
}

/**
 * Group records that describe the same physical property.
 *
 * Two records match when building, locality, bedroom count, floor and building
 * height all agree and the carpet area is *exactly* equal once both sides are
 * expressed in the same unit. Exactness matters: relaxing it to even 0.5% starts
 * swallowing neighbouring flats, because same-size units in one building differ
 * by only a few square feet.
 */
export function clusterDuplicates(listings) {
  const blocks = new Map();
  for (const x of listings) {
    const k = [normaliseName(x.apartment_name), x.locality, x.bedroom, x.floor, x.total_floors].join("|");
    if (!blocks.has(k)) blocks.set(k, []);
    blocks.get(k).push(x);
  }

  const parent = new Map();
  for (const x of listings) parent.set(x.listing_id, x.listing_id);
  const find = (a) => {
    while (parent.get(a) !== a) {
      parent.set(a, parent.get(parent.get(a)));
      a = parent.get(a);
    }
    return a;
  };
  const union = (a, b) => {
    const ra = find(a);
    const rb = find(b);
    if (ra !== rb) parent.set(ra, rb);
  };

  for (const group of blocks.values()) {
    if (group.length < 2) continue;
    for (let i = 0; i < group.length; i++) {
      for (let j = i + 1; j < group.length; j++) {
        if (sameArea(group[i], group[j])) union(group[i].listing_id, group[j].listing_id);
      }
    }
  }

  const clusters = new Map();
  for (const x of listings) {
    const root = find(x.listing_id);
    if (!clusters.has(root)) clusters.set(root, []);
    clusters.get(root).push(x.listing_id);
  }
  return [...clusters.values()].filter((c) => c.length > 1).map((c) => c.sort());
}

/* ------------------------------------------------------------- normalisers */

export function normaliseListing(x, ctx) {
  const sqm = areaIsSqm(x, ctx.bands);
  const out = { ...x };

  out._raw_carpet = x.carpet_area;
  out._area_in_sqm = sqm;
  if (sqm) {
    out.carpet_area = Math.round(x.carpet_area * SQFT_PER_SQM);
    out.super_built_up_area = Math.round(x.super_built_up_area * SQFT_PER_SQM);
    out.area_unit_corrected = true;
  }

  // Eleven records carry the two coordinates the wrong way round.
  if (x.latitude > 50) {
    out.latitude = x.longitude;
    out.longitude = x.latitude;
    out.coordinates_corrected = true;
  }

  out.price_per_sqft =
    out.carpet_area > 0 && out.price > 0 ? Math.round(out.price / out.carpet_area) : null;
  out.posted_date_ist = istDate(x.posted_at);
  out.corruption = corruptionReasons(x);
  out.is_corrupt = out.corruption.length > 0;
  out.is_fake = ctx.fakePhones.has(x.posted_by_contact);
  return out;
}

/**
 * Project money is published in crores, not rupees, except six projects whose
 * `price_min` is in lakhs. The API's own `price_min` sort confirms it: it orders
 * those six *below* every 1.0-crore project.
 */
export function normaliseProject(p) {
  const out = { ...p };
  const minInLakhs = p.price_min > p.price_max * 2 && p.price_min > 20;
  out.price_min_inr = Math.round(p.price_min * (minInLakhs ? RUPEES_PER_LAKH : RUPEES_PER_CRORE));
  out.price_max_inr = Math.round(p.price_max * RUPEES_PER_CRORE);
  out.price_min_unit_corrected = minInLakhs;
  return out;
}

/**
 * zerobroker publishes `deposit` as a number of months' rent; the other four
 * portals publish rupees. Every portal's rupee deposits sit at exactly six times
 * the rent, so a deposit under 100 can only be a month count.
 */
export function normaliseRental(r) {
  const out = { ...r };
  const inMonths = r.deposit > 0 && r.deposit < 100;
  out.deposit_months = inMonths
    ? r.deposit
    : r.price > 0
      ? Number((r.deposit / r.price).toFixed(1))
      : null;
  out.deposit_inr = inMonths ? r.deposit * r.price : r.deposit;
  out.deposit_unit_corrected = inMonths;
  out.posted_date_ist = istDate(r.posted_at);
  // The `title` names a locality chosen at random; `locality` is the real one.
  out.title_locality_mismatch = Boolean(r.title && !r.title.toLowerCase().includes(r.locality));
  return out;
}
