/**
 * In-memory dataset.
 *
 * Every collection is paged to its true end once, corrected, indexed, and then
 * served from memory. This is deliberate rather than lazy: the upstream filters
 * for furnishing and price are accepted but ignored, `total` under-reports, and
 * `limit` silently caps at 50 — so filtering and counting have to happen here if
 * the numbers on screen are going to be right.
 */
import { fetchAll, login, refresh } from "./upstream.js";
import { CACHE_TTL_MS, SERVICE_EMAIL, SERVICE_PASSWORD } from "./config.js";
import {
  clusterDuplicates,
  findFakePhones,
  learnAreaBands,
  normaliseListing,
  normaliseProject,
  normaliseRental,
} from "./normalize.js";

let cache = null;
let building = null;

/** A token used only for cache fills, refreshed as needed. */
const service = { access: null, refresh: null, expiresAt: 0 };

async function serviceToken() {
  const now = Date.now();
  if (service.access && now < service.expiresAt - 60_000) return service.access;

  if (service.refresh) {
    try {
      const r = await refresh(service.refresh);
      service.access = r.access_token;
      service.refresh = r.refresh_token || service.refresh;
      service.expiresAt = now + (r.expires_in || 900) * 1000;
      return service.access;
    } catch {
      /* fall through to a fresh login */
    }
  }
  const r = await login(SERVICE_EMAIL, SERVICE_PASSWORD);
  service.access = r.access_token;
  service.refresh = r.refresh_token;
  service.expiresAt = now + (r.expires_in || 900) * 1000;
  return service.access;
}

async function build() {
  const started = Date.now();
  const token = await serviceToken();

  const [rawListings, rawRentals, rawProjects] = await Promise.all([
    fetchAll("/v1/listings", { token }),
    fetchAll("/v1/rentals", { token }),
    fetchAll("/v1/projects", { token }),
  ]);

  const bands = learnAreaBands(rawListings);
  const fakePhones = findFakePhones(rawListings);
  const ctx = { bands, fakePhones };

  const listings = rawListings.map((x) => normaliseListing(x, ctx));
  const rentals = rawRentals.map(normaliseRental);
  const projects = rawProjects.map(normaliseProject);

  // Mark every record in a duplicate cluster, keeping the earliest-posted one
  // as the canonical record so counts of distinct properties are stable.
  const clusters = clusterDuplicates(listings);
  const byId = new Map(listings.map((x) => [x.listing_id, x]));
  for (const cluster of clusters) {
    const members = cluster.map((id) => byId.get(id));
    members.sort((a, b) => new Date(a.posted_at) - new Date(b.posted_at));
    members.forEach((m, i) => {
      m.duplicate_of = i === 0 ? null : members[0].listing_id;
      m.duplicate_group = cluster;
      m.is_duplicate = i !== 0;
    });
  }

  // Live listings per project: the count `total_listings` is supposed to match.
  const liveByProject = new Map();
  for (const x of listings) {
    if (!x.project_id || !x.is_live) continue;
    liveByProject.set(x.project_id, (liveByProject.get(x.project_id) || 0) + 1);
  }
  for (const p of projects) {
    p.actual_live_listings = liveByProject.get(p.project_id) || 0;
    p.listing_count_matches = p.total_listings === p.actual_live_listings;
  }

  cache = {
    listings,
    rentals,
    projects,
    clusters,
    listingsById: byId,
    rentalsById: new Map(rentals.map((x) => [x.listing_id, x])),
    projectsById: new Map(projects.map((x) => [x.project_id, x])),
    localities: [...new Set(listings.map((x) => x.locality))].sort(),
    builtAt: Date.now(),
    buildMs: Date.now() - started,
  };
  return cache;
}

export async function getDataset({ force = false } = {}) {
  if (!force && cache && Date.now() - cache.builtAt < CACHE_TTL_MS) return cache;
  if (building) return building;
  building = build().finally(() => {
    building = null;
  });
  return building;
}

export function peekDataset() {
  return cache;
}
