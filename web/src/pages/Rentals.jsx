import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import useApiData from "../components/useApiData.js";
import { qs } from "../lib/api.js";
import { bhkLabel, inrExact, istDay, sqft, titleCase } from "../lib/format.js";

const LOCALITIES = [
  "andheri west", "bandra east", "borivali west", "chembur", "goregaon east",
  "kandivali east", "malad west", "mulund west", "powai", "thane west",
];
const FURNISHINGS = ["unfurnished", "semi-furnished", "fully-furnished"];

export default function Rentals() {
  const [params, setParams] = useSearchParams();
  const get = (k, d = "") => params.get(k) ?? d;

  const query = useMemo(
    () =>
      qs({
        locality: get("locality"),
        bedroom: get("bedroom"),
        furnishing: get("furnishing"),
        min_price: get("min_price"),
        max_price: get("max_price"),
        sort_by: get("sort_by", "price"),
        order: get("order", "asc"),
        page: get("page", "1"),
        limit: 30,
      }),
    [params]
  );

  const { data, loading, error } = useApiData(`/api/rentals${query}`);

  function update(patch) {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v === "" || v == null) next.delete(k);
      else next.set(k, v);
    }
    if (!("page" in patch)) next.delete("page");
    setParams(next, { replace: true });
  }

  const page = Number(get("page", "1"));

  return (
    <main className="page">
      <div className="page-head">
        <h1>Homes to rent</h1>
        <p>
          Rent is monthly, in rupees. Deposits are shown in rupees and in months — one portal
          publishes the deposit as a month count rather than an amount, so both are given to make
          the two comparable.
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
            {[1, 2, 3, 4, 5].map((b) => (
              <option key={b} value={b}>{b} BHK</option>
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
          <label>Min rent (₹)</label>
          <input className="input" type="number" min="0" step="1000" value={get("min_price")}
            onChange={(e) => update({ min_price: e.target.value })} />
        </div>
        <div className="field">
          <label>Max rent (₹)</label>
          <input className="input" type="number" min="0" step="1000" value={get("max_price")}
            onChange={(e) => update({ max_price: e.target.value })} />
        </div>
        <div className="filters-actions">
          <button className="btn" onClick={() => setParams(new URLSearchParams(), { replace: true })}>Reset</button>
        </div>
      </div>

      <div className="toolbar">
        <span className="toolbar-count">
          {loading ? "Loading…" : `${(data?.total ?? 0).toLocaleString("en-IN")} rentals`}
        </span>
        <div className="toolbar-spacer" />
        <select
          className="select"
          style={{ width: "auto" }}
          value={`${get("sort_by", "price")}:${get("order", "asc")}`}
          onChange={(e) => {
            const [sort_by, order] = e.target.value.split(":");
            update({ sort_by, order });
          }}
        >
          <option value="price:asc">Rent: low to high</option>
          <option value="price:desc">Rent: high to low</option>
          <option value="deposit:asc">Deposit: low to high</option>
          <option value="carpet_area:desc">Largest first</option>
        </select>
      </div>

      {error && <div className="notice notice-danger">{error}</div>}
      {loading && <div className="spinner">Loading rentals…</div>}

      {!loading && data && (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Property</th>
                  <th>Locality</th>
                  <th>Config</th>
                  <th className="num">Carpet</th>
                  <th className="num">Rent / month</th>
                  <th className="num">Deposit</th>
                  <th>Furnishing</th>
                  <th>Posted</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((r) => (
                  <tr key={r.listing_id}>
                    <td>{r.apartment_name}</td>
                    <td>{titleCase(r.locality)}</td>
                    <td>{bhkLabel(r.bedroom)}</td>
                    <td className="num">{sqft(r.carpet_area)}</td>
                    <td className="num">{inrExact(r.price)}</td>
                    <td className="num">
                      {inrExact(r.deposit_inr)}
                      <span className="faint"> · {r.deposit_months} mo</span>
                      {r.deposit_unit_corrected && <span className="pill pill-accent" style={{ marginLeft: 6 }}>conv</span>}
                    </td>
                    <td>{titleCase(r.furnishing)}</td>
                    <td>{istDay(r.posted_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pager">
            <button className="btn btn-sm" disabled={page <= 1} onClick={() => update({ page: page - 1 })}>Previous</button>
            <span>Page {data.page} of {data.total_pages}</span>
            <button className="btn btn-sm" disabled={page >= data.total_pages} onClick={() => update({ page: page + 1 })}>Next</button>
          </div>
        </>
      )}
    </main>
  );
}
