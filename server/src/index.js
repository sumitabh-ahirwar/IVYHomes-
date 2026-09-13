/**
 * API server.
 *
 * The browser never talks to solve.ivy.homes directly: the API key is a
 * server-side secret, and the filtering, unit correction and counting all have
 * to happen somewhere the upstream quirks can be absorbed. User sessions are
 * still real — /api/auth/login forwards the credentials upstream and hands back
 * the upstream tokens, which the client replays on every request.
 */
import express from "express";
import compression from "compression";
import cors from "cors";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { PORT, REFERENCE_ISO } from "./config.js";
import { call, login, refresh } from "./upstream.js";
import { getDataset, peekDataset } from "./dataset.js";
import { buildAnalytics } from "./analytics.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(compression());
app.use(cors());
app.use(express.json());

const asyncRoute = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

function bearer(req) {
  const h = req.header("authorization") || "";
  return h.startsWith("Bearer ") ? h.slice(7) : null;
}

function requireToken(req, res, next) {
  if (!bearer(req)) return res.status(401).json({ detail: "not signed in" });
  next();
}

/* ---------------------------------------------------------------- auth ---- */

app.post(
  "/api/auth/login",
  asyncRoute(async (req, res) => {
    const { email, password } = req.body || {};
    if (!email || !password) return res.status(400).json({ detail: "email and password are required" });
    const r = await login(email, password);
    res.json({
      access_token: r.access_token,
      refresh_token: r.refresh_token,
      // 900 seconds, not the 86400 the reference claims - the client has to
      // refresh for a session to outlive a coffee break.
      expires_in: r.expires_in,
      user: r.user,
    });
  })
);

app.post(
  "/api/auth/refresh",
  asyncRoute(async (req, res) => {
    const { refresh_token } = req.body || {};
    if (!refresh_token) return res.status(400).json({ detail: "refresh_token is required" });
    const r = await refresh(refresh_token);
    res.json({
      access_token: r.access_token,
      refresh_token: r.refresh_token || refresh_token,
      expires_in: r.expires_in,
      user: r.user,
    });
  })
);

app.post(
  "/api/auth/logout",
  requireToken,
  asyncRoute(async (req, res) => {
    // Upstream accepts this but the token stays valid, so the client discarding
    // it is what actually ends the session.
    try {
      await call("/auth/logout", { method: "POST", token: bearer(req) });
    } catch {
      /* logging out should never fail the user */
    }
    res.json({ ok: true });
  })
);

app.get(
  "/api/me",
  requireToken,
  asyncRoute(async (req, res) => {
    res.json(await call("/v1/me", { token: bearer(req) }));
  })
);

/* ------------------------------------------------------------ listings ---- */

const num = (v) => (v === undefined || v === "" ? null : Number(v));

function filterListings(listings, q) {
  const locality = q.locality || null;
  const bedroom = num(q.bedroom);
  const type = q.property_type || null;
  const furnishing = q.furnishing || null;
  const minPrice = num(q.min_price);
  const maxPrice = num(q.max_price);
  const minArea = num(q.min_area);
  const search = (q.q || "").trim().toLowerCase();
  // Bait, impossible records and second copies are hidden unless asked for.
  const includeFake = q.include_fake === "true";
  const includeCorrupt = q.include_corrupt === "true";
  const includeDuplicates = q.include_duplicates === "true";
  const includeInactive = q.include_inactive === "true";

  return listings.filter((x) => {
    if (!includeInactive && !x.is_live) return false;
    if (!includeFake && x.is_fake) return false;
    if (!includeCorrupt && x.is_corrupt) return false;
    if (!includeDuplicates && x.is_duplicate) return false;
    if (locality && x.locality !== locality) return false;
    if (bedroom !== null && x.bedroom !== bedroom) return false;
    if (type && x.property_type !== type) return false;
    if (furnishing && x.furnishing !== furnishing) return false;
    if (minPrice !== null && x.price < minPrice) return false;
    if (maxPrice !== null && x.price > maxPrice) return false;
    if (minArea !== null && x.carpet_area < minArea) return false;
    if (search) {
      const hay = `${x.apartment_name} ${x.locality} ${x.listing_id} ${x.description}`.toLowerCase();
      if (!hay.includes(search)) return false;
    }
    return true;
  });
}

const SORTS = {
  price: (a, b) => a.price - b.price,
  carpet_area: (a, b) => a.carpet_area - b.carpet_area,
  price_per_sqft: (a, b) => (a.price_per_sqft || 0) - (b.price_per_sqft || 0),
  bedroom: (a, b) => a.bedroom - b.bedroom,
  // Sorted on the full instant, not the IST calendar date the API stops at.
  posted_at: (a, b) => new Date(a.posted_at) - new Date(b.posted_at),
};

function paginate(rows, q) {
  const page = Math.max(1, num(q.page) || 1);
  const limit = Math.min(100, Math.max(1, num(q.limit) || 24));
  const start = (page - 1) * limit;
  return {
    total: rows.length,
    page,
    page_size: limit,
    total_pages: Math.max(1, Math.ceil(rows.length / limit)),
    results: rows.slice(start, start + limit),
  };
}

app.get(
  "/api/listings",
  requireToken,
  asyncRoute(async (req, res) => {
    const ds = await getDataset();
    let rows = filterListings(ds.listings, req.query);
    const cmp = SORTS[req.query.sort_by] || SORTS.posted_at;
    rows = [...rows].sort(cmp);
    if ((req.query.order || "desc") === "desc") rows.reverse();
    res.json(paginate(rows, req.query));
  })
);

app.get(
  "/api/listings/:id",
  requireToken,
  asyncRoute(async (req, res) => {
    const ds = await getDataset();
    const listing = ds.listingsById.get(req.params.id);
    if (!listing) return res.status(404).json({ detail: "no such listing in your city" });

    // The documented /similar endpoint does not exist, so comparables are
    // computed here: same locality, same bedroom count, price within 15%.
    const similar = ds.listings
      .filter(
        (x) =>
          x.listing_id !== listing.listing_id &&
          x.locality === listing.locality &&
          x.bedroom === listing.bedroom &&
          x.is_live &&
          !x.is_fake &&
          !x.is_corrupt &&
          !x.is_duplicate &&
          listing.price > 0 &&
          Math.abs(x.price - listing.price) / listing.price <= 0.15
      )
      .slice(0, 10);

    const duplicates = (listing.duplicate_group || [])
      .filter((id) => id !== listing.listing_id)
      .map((id) => ds.listingsById.get(id))
      .filter(Boolean);

    res.json({
      listing,
      similar,
      duplicates,
      project: listing.project_id ? ds.projectsById.get(listing.project_id) || null : null,
    });
  })
);

/* ------------------------------------------------------------- rentals ---- */

app.get(
  "/api/rentals",
  requireToken,
  asyncRoute(async (req, res) => {
    const ds = await getDataset();
    const bedroom = num(req.query.bedroom);
    const minPrice = num(req.query.min_price);
    const maxPrice = num(req.query.max_price);
    let rows = ds.rentals.filter((r) => {
      if (req.query.include_inactive !== "true" && !r.is_live) return false;
      if (req.query.locality && r.locality !== req.query.locality) return false;
      if (bedroom !== null && r.bedroom !== bedroom) return false;
      if (req.query.furnishing && r.furnishing !== req.query.furnishing) return false;
      if (minPrice !== null && r.price < minPrice) return false;
      if (maxPrice !== null && r.price > maxPrice) return false;
      return true;
    });
    const key = req.query.sort_by === "carpet_area" ? "carpet_area" : req.query.sort_by === "deposit" ? "deposit_inr" : "price";
    rows = [...rows].sort((a, b) => (a[key] || 0) - (b[key] || 0));
    if ((req.query.order || "asc") === "desc") rows.reverse();
    res.json(paginate(rows, req.query));
  })
);

app.get(
  "/api/rentals/:id",
  requireToken,
  asyncRoute(async (req, res) => {
    const ds = await getDataset();
    const rental = ds.rentalsById.get(req.params.id);
    if (!rental) return res.status(404).json({ detail: "no such rental in your city" });
    res.json({ rental });
  })
);

/* ------------------------------------------------------------ projects ---- */

app.get(
  "/api/projects",
  requireToken,
  asyncRoute(async (req, res) => {
    const ds = await getDataset();
    let rows = ds.projects.filter((p) => {
      if (req.query.locality && p.locality !== req.query.locality) return false;
      if (req.query.project_status && p.project_status !== req.query.project_status) return false;
      if (req.query.mismatched === "true" && p.listing_count_matches) return false;
      return true;
    });
    const key =
      { price_min: "price_min_inr", price_max: "price_max_inr", total_units: "total_units", launch_date: "launch_date" }[
        req.query.sort_by
      ] || "price_max_inr";
    rows = [...rows].sort((a, b) => (a[key] > b[key] ? 1 : a[key] < b[key] ? -1 : 0));
    if ((req.query.order || "desc") === "desc") rows.reverse();
    res.json(paginate(rows, req.query));
  })
);

app.get(
  "/api/projects/:id",
  requireToken,
  asyncRoute(async (req, res) => {
    const ds = await getDataset();
    const project = ds.projectsById.get(req.params.id);
    if (!project) return res.status(404).json({ detail: "no such project in your city" });
    const listings = ds.listings.filter((x) => x.project_id === project.project_id);
    res.json({ project, listings });
  })
);

/* --------------------------------------------------------------- saved ---- */

// Upstream calls this /v1/saved, not the documented /v1/favourites, and its
// POST body field is `listing_id`, not `id`. Saves live upstream, per user, so
// they survive a reload and a re-login.

app.get(
  "/api/saved",
  requireToken,
  asyncRoute(async (req, res) => {
    const ds = await getDataset();
    const saved = await call("/v1/saved", { token: bearer(req) });
    const results = (saved.results || []).map(
      (r) => ds.listingsById.get(r.listing_id) || r
    );
    res.json({ count: saved.count ?? results.length, results });
  })
);

app.post(
  "/api/saved",
  requireToken,
  asyncRoute(async (req, res) => {
    const id = req.body?.listing_id;
    if (!id) return res.status(400).json({ detail: "listing_id is required" });
    res.json(await call("/v1/saved", { method: "POST", token: bearer(req), body: { listing_id: id } }));
  })
);

app.delete(
  "/api/saved/:id",
  requireToken,
  asyncRoute(async (req, res) => {
    res.json(await call(`/v1/saved/${encodeURIComponent(req.params.id)}`, { method: "DELETE", token: bearer(req) }));
  })
);

/* ------------------------------------------------------------ insights ---- */

app.get(
  "/api/insights",
  requireToken,
  asyncRoute(async (req, res) => {
    res.json(buildAnalytics(await getDataset()));
  })
);

app.get(
  "/api/meta",
  asyncRoute(async (req, res) => {
    const ds = peekDataset();
    res.json({
      reference: REFERENCE_ISO,
      localities: ds ? ds.localities : [],
      dataset_ready: Boolean(ds),
      built_at: ds ? new Date(ds.builtAt).toISOString() : null,
    });
  })
);

app.get("/api/health", (req, res) => res.json({ ok: true, dataset_ready: Boolean(peekDataset()) }));

/* ---------------------------------------------------------- static app ---- */

const webDist = path.resolve(__dirname, "../../web/dist");
app.use(express.static(webDist));
app.get(/^(?!\/api\/).*/, (req, res) => res.sendFile(path.join(webDist, "index.html")));

/* --------------------------------------------------------------- errors --- */

app.use((err, req, res, _next) => {
  const status = err.status || 500;
  if (status >= 500) console.error("[error]", err.message);
  res.status(status).json({ detail: err.message || "server error" });
});

app.listen(PORT, () => {
  console.log(`api listening on :${PORT}`);
  getDataset()
    .then((ds) =>
      console.log(
        `dataset warm: ${ds.listings.length} listings, ${ds.rentals.length} rentals, ` +
          `${ds.projects.length} projects in ${ds.buildMs}ms`
      )
    )
    .catch((e) => console.error("dataset warm failed:", e.message));
});
