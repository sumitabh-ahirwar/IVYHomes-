import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import useApiData from "../components/useApiData.js";
import ListingCard from "../components/ListingCard.jsx";
import { qs } from "../lib/api.js";
import { titleCase } from "../lib/format.js";

const LOCALITIES = [
  "andheri west", "bandra east", "borivali west", "chembur", "goregaon east",
  "kandivali east", "malad west", "mulund west", "powai", "thane west",
];
const TYPES = ["apartment", "villa", "independent house", "builder floor", "plot"];
const FURNISHINGS = ["unfurnished", "semi-furnished", "fully-furnished"];

export default function Listings() {
  const [params, setParams] = useSearchParams();
  const get = (k, d = "") => params.get(k) ?? d;

  const query = useMemo(
    () =>
      qs({
        locality: get("locality"),
        bedroom: get("bedroom"),
        property_type: get("property_type"),
        furnishing: get("furnishing"),
        min_price: get("min_price"),
        max_price: get("max_price"),
        q: get("q"),
        sort_by: get("sort_by", "posted_at"),
        order: get("order", "desc"),
        page: get("page", "1"),
        limit: 24,
        include_fake: get("include_fake"),
        include_duplicates: get("include_duplicates"),
        include_inactive: get("include_inactive"),
      }),
    [params]
  );

  const { data, loading, error } = useApiData(`/api/listings${query}`);

  function update(patch) {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v === "" || v === false || v === null || v === undefined) next.delete(k);
      else next.set(k, v);
    }
    // Any change to the query resets to the first page.
    if (!("page" in patch)) next.delete("page");
    setParams(next, { replace: true });
  }

  const page = Number(get("page", "1"));

  return (
    <main className="page">
      <div className="page-head">
        <h1>Properties for sale</h1>
        <p>
          Every filter here is applied over the full set of records, paged to the end rather than
          trusting the reported total. Bait listings, impossible records and repeat postings are
          hidden by default — use the toggles to see them.
        </p>
      </div>

      <div className="card filters">
        <div className="field">
          <label>Locality</label>
          <select className="select" value={get("locality")} onChange={(e) => update({ locality: e.target.value })}>
            <option value="">Any locality</option>
            {LOCALITIES.map((l) => (
              <option key={l} value={l}>{titleCase(l)}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Bedrooms</label>
          <select className="select" value={get("bedroom")} onChange={(e) => update({ bedroom: e.target.value })}>
            <option value="">Any</option>
            <option value="0">Plot</option>
            {[1, 2, 3, 4, 5].map((b) => (
              <option key={b} value={b}>{b} BHK</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Property type</label>
          <select className="select" value={get("property_type")} onChange={(e) => update({ property_type: e.target.value })}>
            <option value="">Any type</option>
            {TYPES.map((t) => (
              <option key={t} value={t}>{titleCase(t)}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Furnishing</label>
          <select className="select" value={get("furnishing")} onChange={(e) => update({ furnishing: e.target.value })}>
            <option value="">Any</option>
            {FURNISHINGS.map((f) => (
              <option key={f} value={f}>{titleCase(f)}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Min price (₹)</label>
          <input
            className="input"
            type="number"
            min="0"
            step="100000"
            placeholder="e.g. 20000000"
            value={get("min_price")}
            onChange={(e) => update({ min_price: e.target.value })}
          />
        </div>

        <div className="field">
          <label>Max price (₹)</label>
          <input
            className="input"
            type="number"
            min="0"
            step="100000"
            placeholder="e.g. 60000000"
            value={get("max_price")}
            onChange={(e) => update({ max_price: e.target.value })}
          />
        </div>

        <div className="field">
          <label>Search</label>
          <input
            className="input"
            placeholder="Building or id"
            value={get("q")}
            onChange={(e) => update({ q: e.target.value })}
          />
        </div>

        <div className="filters-actions">
          <button className="btn" onClick={() => setParams(new URLSearchParams(), { replace: true })}>
            Reset
          </button>
        </div>
      </div>

      <div className="toolbar">
        <span className="toolbar-count">
          {loading ? "Loading…" : `${(data?.total ?? 0).toLocaleString("en-IN")} matching listings`}
        </span>

        <div className="toggles">
          <label>
            <input
              type="checkbox"
              checked={get("include_fake") === "true"}
              onChange={(e) => update({ include_fake: e.target.checked ? "true" : "" })}
            />
            Show suspected bait
          </label>
          <label>
            <input
              type="checkbox"
              checked={get("include_duplicates") === "true"}
              onChange={(e) => update({ include_duplicates: e.target.checked ? "true" : "" })}
            />
            Show repeat postings
          </label>
          <label>
            <input
              type="checkbox"
              checked={get("include_inactive") === "true"}
              onChange={(e) => update({ include_inactive: e.target.checked ? "true" : "" })}
            />
            Include inactive
          </label>
        </div>

        <div className="toolbar-spacer" />

        <select
          className="select"
          style={{ width: "auto" }}
          value={`${get("sort_by", "posted_at")}:${get("order", "desc")}`}
          onChange={(e) => {
            const [sort_by, order] = e.target.value.split(":");
            update({ sort_by, order });
          }}
        >
          <option value="posted_at:desc">Newest first</option>
          <option value="posted_at:asc">Oldest first</option>
          <option value="price:asc">Price: low to high</option>
          <option value="price:desc">Price: high to low</option>
          <option value="price_per_sqft:asc">₹/sq ft: low to high</option>
          <option value="carpet_area:desc">Largest first</option>
        </select>
      </div>

      {error && <div className="notice notice-danger">{error}</div>}
      {loading && <div className="spinner">Loading listings…</div>}

      {!loading && data && data.results.length === 0 && (
        <div className="card empty">No listings match these filters.</div>
      )}

      {!loading && data && data.results.length > 0 && (
        <>
          <div className="grid">
            {data.results.map((l) => (
              <ListingCard key={l.listing_id} listing={l} />
            ))}
          </div>

          <div className="pager">
            <button className="btn btn-sm" disabled={page <= 1} onClick={() => update({ page: page - 1 })}>
              Previous
            </button>
            <span>
              Page {data.page} of {data.total_pages}
            </span>
            <button
              className="btn btn-sm"
              disabled={page >= data.total_pages}
              onClick={() => update({ page: page + 1 })}
            >
              Next
            </button>
          </div>
        </>
      )}
    </main>
  );
}
