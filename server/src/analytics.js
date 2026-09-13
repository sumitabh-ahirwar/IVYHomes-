/**
 * The insights payload.
 *
 * `/v1/analytics/summary` is documented but does not exist, so everything the
 * reference promised is computed here from the corrected dataset, alongside the
 * data-quality figures a user of this site would actually want to know before
 * trusting a price.
 */
import { REFERENCE } from "./normalize.js";

const median = (arr) => {
  if (!arr.length) return null;
  const s = [...arr].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : Math.round((s[m - 1] + s[m]) / 2);
};

export function buildAnalytics(ds) {
  const { listings, rentals, projects, clusters } = ds;

  // Trustworthy = a live listing that is neither impossible nor lead-generation
  // bait, and is not a second copy of a property already counted.
  const trusted = listings.filter((x) => x.is_live && !x.is_corrupt && !x.is_fake && !x.is_duplicate);
  const prices = trusted.map((x) => x.price).filter((p) => p > 0);
  const ppsf = trusted.map((x) => x.price_per_sqft).filter(Boolean);

  const byLocality = ds.localities
    .map((locality) => {
      const rows = trusted.filter((x) => x.locality === locality);
      const rentRows = rentals.filter((r) => r.locality === locality && r.is_live);
      return {
        locality,
        count: listings.filter((x) => x.locality === locality).length,
        trusted_count: rows.length,
        median_price: median(rows.map((x) => x.price)),
        median_price_per_sqft: median(rows.map((x) => x.price_per_sqft).filter(Boolean)),
        median_rent: median(rentRows.map((r) => r.price)),
      };
    })
    .sort((a, b) => b.count - a.count);

  const byBhk = [...new Set(listings.map((x) => x.bedroom))]
    .sort((a, b) => a - b)
    .map((bedroom) => {
      const rows = trusted.filter((x) => x.bedroom === bedroom);
      return {
        bedroom,
        count: rows.length,
        median_price: median(rows.map((x) => x.price)),
        median_price_per_sqft: median(rows.map((x) => x.price_per_sqft).filter(Boolean)),
      };
    });

  const byType = [...new Set(listings.map((x) => x.property_type))].sort().map((property_type) => ({
    property_type,
    count: trusted.filter((x) => x.property_type === property_type).length,
  }));

  // Postings per IST day over the eight weeks before the reference moment.
  const dayCounts = new Map();
  for (const x of listings) dayCounts.set(x.posted_date_ist, (dayCounts.get(x.posted_date_ist) || 0) + 1);
  const timeline = [...dayCounts.entries()]
    .map(([date, count]) => ({ date, count }))
    .filter((d) => d.date < REFERENCE.toISOString().slice(0, 10))
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-56);

  const sevenDaysAgo = new Date(REFERENCE.getTime() - 7 * 86400_000);
  const lastSeven = listings.filter((x) => {
    const t = new Date(x.posted_at);
    return t >= sevenDaysAgo && t < REFERENCE;
  }).length;

  const fakeListings = listings.filter((x) => x.is_fake);
  const fakePhones = [...new Set(fakeListings.map((x) => x.posted_by_contact))].map((phone) => {
    const rows = fakeListings.filter((x) => x.posted_by_contact === phone);
    return {
      phone,
      listings: rows.length,
      identities: [...new Set(rows.map((x) => x.posted_by_name))].sort(),
      median_price_per_sqft: median(rows.map((x) => x.price_per_sqft).filter(Boolean)),
    };
  });

  const corruptionTally = {};
  for (const x of listings) {
    for (const reason of x.corruption) corruptionTally[reason] = (corruptionTally[reason] || 0) + 1;
  }

  return {
    city: "mumbai",
    reference: REFERENCE.toISOString(),
    generated_at: new Date().toISOString(),

    // What the documented endpoint promised.
    total_listings: listings.length,
    median_price: median(prices),
    median_price_per_sqft: median(ppsf),
    by_locality: byLocality,
    by_bhk: byBhk,
    by_property_type: byType,

    // What a user actually needs to know about this dataset.
    integrity: {
      total_records: listings.length,
      live: listings.filter((x) => x.is_live).length,
      not_live: listings.filter((x) => !x.is_live).length,
      corrupt: listings.filter((x) => x.is_corrupt).length,
      fake: fakeListings.length,
      duplicate_records: listings.filter((x) => x.is_duplicate).length,
      duplicate_clusters: clusters.length,
      distinct_properties: listings.length - listings.filter((x) => x.is_duplicate).length,
      trusted: trusted.length,
      corruption_breakdown: corruptionTally,
      fake_operations: fakePhones,
      area_unit_corrected: listings.filter((x) => x.area_unit_corrected).length,
      coordinates_corrected: listings.filter((x) => x.coordinates_corrected).length,
    },

    rentals: {
      total: rentals.length,
      live: rentals.filter((r) => r.is_live).length,
      median_rent: median(rentals.map((r) => r.price)),
      deposit_unit_corrected: rentals.filter((r) => r.deposit_unit_corrected).length,
      title_locality_mismatch: rentals.filter((r) => r.title_locality_mismatch).length,
    },

    projects: {
      total: projects.length,
      price_min_unit_corrected: projects.filter((p) => p.price_min_unit_corrected).length,
      listing_count_wrong: projects.filter((p) => !p.listing_count_matches).length,
      costliest: [...projects]
        .sort((a, b) => b.price_max_inr - a.price_max_inr)
        .slice(0, 5)
        .map((p) => ({
          project_id: p.project_id,
          apartment_name: p.apartment_name,
          locality: p.locality,
          price_max_inr: p.price_max_inr,
        })),
    },

    activity: { timeline, listings_last_7_days: lastSeven },
  };
}
