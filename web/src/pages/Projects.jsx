import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import useApiData from "../components/useApiData.js";
import { qs } from "../lib/api.js";
import { inr, sqft, titleCase } from "../lib/format.js";

const LOCALITIES = [
  "andheri west", "bandra east", "borivali west", "chembur", "goregaon east",
  "kandivali east", "malad west", "mulund west", "powai", "thane west",
];
const STATUSES = ["new launch", "under construction", "ready to move"];

export default function Projects() {
  const [params, setParams] = useSearchParams();
  const get = (k, d = "") => params.get(k) ?? d;

  const query = useMemo(
    () =>
      qs({
        locality: get("locality"),
        project_status: get("project_status"),
        mismatched: get("mismatched"),
        sort_by: get("sort_by", "price_max"),
        order: get("order", "desc"),
        page: get("page", "1"),
        limit: 30,
      }),
    [params]
  );

  const { data, loading, error } = useApiData(`/api/projects${query}`);

  function update(patch) {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v === "" || v === false || v == null) next.delete(k);
      else next.set(k, v);
    }
    if (!("page" in patch)) next.delete("page");
    setParams(next, { replace: true });
  }

  const page = Number(get("page", "1"));

  return (
    <main className="page">
      <div className="page-head">
        <h1>Builder projects</h1>
        <p>
          Prices are published in crores rather than rupees, and a handful of projects give their
          minimum in lakhs. Both are converted to rupees here. Each project also reports how many
          listings it has, which is often wrong — the live count is shown beside it.
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
          <label>Status</label>
          <select className="select" value={get("project_status")} onChange={(e) => update({ project_status: e.target.value })}>
            <option value="">Any status</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{titleCase(s)}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Sort by</label>
          <select
            className="select"
            value={`${get("sort_by", "price_max")}:${get("order", "desc")}`}
            onChange={(e) => {
              const [sort_by, order] = e.target.value.split(":");
              update({ sort_by, order });
            }}
          >
            <option value="price_max:desc">Highest max price</option>
            <option value="price_min:asc">Lowest entry price</option>
            <option value="total_units:desc">Largest by units</option>
            <option value="launch_date:desc">Most recently launched</option>
          </select>
        </div>
        <div className="filters-actions">
          <label style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 13 }}>
            <input
              type="checkbox"
              checked={get("mismatched") === "true"}
              onChange={(e) => update({ mismatched: e.target.checked ? "true" : "" })}
            />
            Only wrong counts
          </label>
        </div>
      </div>

      <div className="toolbar">
        <span className="toolbar-count">
          {loading ? "Loading…" : `${(data?.total ?? 0).toLocaleString("en-IN")} projects`}
        </span>
      </div>

      {error && <div className="notice notice-danger">{error}</div>}
      {loading && <div className="spinner">Loading projects…</div>}

      {!loading && data && (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Developer</th>
                  <th>Locality</th>
                  <th>Status</th>
                  <th className="num">Price band</th>
                  <th className="num">Area band</th>
                  <th className="num">Units</th>
                  <th className="num">Listings claimed</th>
                  <th className="num">Actually live</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((p) => (
                  <tr key={p.project_id}>
                    <td>
                      {p.apartment_name}
                      <div className="faint mono">{p.project_id}</div>
                    </td>
                    <td>{p.developer_name}</td>
                    <td>{titleCase(p.locality)}</td>
                    <td>{titleCase(p.project_status)}</td>
                    <td className="num">
                      {inr(p.price_min_inr)} – {inr(p.price_max_inr)}
                      {p.price_min_unit_corrected && (
                        <span className="pill pill-accent" style={{ marginLeft: 6 }}>min conv</span>
                      )}
                    </td>
                    <td className="num">{sqft(p.min_area_sqft)} – {sqft(p.max_area_sqft)}</td>
                    <td className="num">{p.total_units.toLocaleString("en-IN")}</td>
                    <td className="num">{p.total_listings}</td>
                    <td className="num">
                      {p.actual_live_listings}
                      {!p.listing_count_matches && (
                        <span className="pill pill-warn" style={{ marginLeft: 6 }}>mismatch</span>
                      )}
                    </td>
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
