import { Link, useParams } from "react-router-dom";
import useApiData from "../components/useApiData.js";
import { useSession } from "../lib/session.jsx";
import { bhkLabel, inr, inrExact, istDateTime, perSqft, sqft, titleCase } from "../lib/format.js";

export default function ListingDetail() {
  const { id } = useParams();
  const { savedIds, toggleSaved } = useSession();
  const { data, loading, error } = useApiData(`/api/listings/${encodeURIComponent(id)}`);

  if (loading) return <main className="page spinner">Loading listing…</main>;
  if (error) return <main className="page"><div className="notice notice-danger">{error}</div></main>;

  const { listing, similar, duplicates, project } = data;
  const saved = savedIds.has(listing.listing_id);

  return (
    <main className="page">
      <div style={{ marginBottom: 14 }}>
        <Link className="btn btn-ghost btn-sm" to="/listings">← Back to listings</Link>
      </div>

      <div className="detail-grid">
        <div>
          {listing.is_fake && (
            <div className="notice notice-danger">
              <strong>This listing is almost certainly not genuine.</strong>
              It is posted from a phone number that runs {" "}
              <Link to="/insights">a cluster of below-market adverts under several different agent names</Link>,
              and the price is far under the going rate for the area. Treat any request for a booking
              or token amount as a scam.
            </div>
          )}

          {listing.is_corrupt && (
            <div className="notice notice-warn">
              <strong>This record contains impossible values.</strong>
              <ul>
                {listing.corruption.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          {listing.area_unit_corrected && (
            <div className="notice notice-info">
              <strong>Area converted from square metres.</strong>
              This portal publishes areas in square metres while the rest publish square feet. The
              figures below are in square feet; the source value was {listing._raw_carpet} m².
            </div>
          )}

          {!listing.is_live && (
            <div className="notice notice-warn">
              <strong>This listing is no longer live.</strong>
              It is still returned by the API, so it is shown here with the status made explicit.
            </div>
          )}

          <div className="card detail-main">
            <h1>{titleCase(listing.apartment_name)}</h1>
            <div className="muted">
              {titleCase(listing.locality)}, Mumbai · {titleCase(listing.property_type)}
            </div>

            <div className="detail-price">{inr(listing.price)}</div>
            <div className="muted">
              {inrExact(listing.price)} · {perSqft(listing.price_per_sqft)} on carpet area
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
              <button
                className={saved ? "btn" : "btn btn-primary"}
                onClick={() => toggleSaved(listing.listing_id)}
              >
                {saved ? "♥ Saved" : "♡ Save this listing"}
              </button>
              <a className="btn" href={listing.listing_url} target="_blank" rel="noreferrer noopener">
                View on {listing.website} ↗
              </a>
            </div>

            <dl className="spec-grid">
              <div className="spec"><dt>Configuration</dt><dd>{bhkLabel(listing.bedroom)}</dd></div>
              <div className="spec"><dt>Carpet area</dt><dd>{sqft(listing.carpet_area)}</dd></div>
              <div className="spec"><dt>Super built-up</dt><dd>{sqft(listing.super_built_up_area)}</dd></div>
              <div className="spec"><dt>Bathrooms</dt><dd>{listing.bathroom}</dd></div>
              <div className="spec"><dt>Balconies</dt><dd>{listing.balcony}</dd></div>
              <div className="spec"><dt>Floor</dt><dd>{listing.floor} of {listing.total_floors}</dd></div>
              <div className="spec"><dt>Furnishing</dt><dd>{titleCase(listing.furnishing)}</dd></div>
              <div className="spec"><dt>Facing</dt><dd>{titleCase(listing.facing_direction)}</dd></div>
              <div className="spec"><dt>Covered parking</dt><dd>{listing.covered_parking}</dd></div>
            </dl>

            <h3 style={{ fontSize: 14, margin: "0 0 6px" }}>Description</h3>
            {/* Seller-written text. Rendered as plain text, never interpreted. */}
            <p className="muted" style={{ marginTop: 0, whiteSpace: "pre-wrap" }}>
              {listing.description}
            </p>
          </div>

          {duplicates.length > 0 && (
            <div className="card side-card" style={{ marginTop: 14 }}>
              <h3>Also posted as</h3>
              <p className="muted" style={{ marginTop: -6, fontSize: 13 }}>
                The same flat — same building, floor and carpet area — advertised again elsewhere.
              </p>
              <div className="mini-list">
                {duplicates.map((d) => (
                  <Link className="mini" key={d.listing_id} to={`/listings/${d.listing_id}`}>
                    <span>
                      <span className="mono">{d.listing_id}</span> · {d.website}
                    </span>
                    <span>{inr(d.price)}</span>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {similar.length > 0 && (
            <div className="card side-card" style={{ marginTop: 14 }}>
              <h3>Comparable homes</h3>
              <div className="mini-list">
                {similar.map((s) => (
                  <Link className="mini" key={s.listing_id} to={`/listings/${s.listing_id}`}>
                    <span>{titleCase(s.apartment_name)} · {sqft(s.carpet_area)}</span>
                    <span>{inr(s.price)}</span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        <aside>
          <div className="card side-card">
            <h3>Listed by</h3>
            <div className="kv"><span>Name</span><span>{listing.posted_by_name}</span></div>
            <div className="kv"><span>Role</span><span>{titleCase(listing.posted_by)}</span></div>
            <div className="kv"><span>Contact</span><span className="mono">{listing.posted_by_contact}</span></div>
            <div className="kv"><span>Source</span><span>{listing.website}</span></div>
            <div className="kv">
              <span>Verified badge</span>
              <span>{listing.is_verified ? "Yes" : "No"}</span>
            </div>
            {listing.is_verified && listing.is_fake && (
              <p className="muted" style={{ fontSize: 12.5, marginBottom: 0 }}>
                The verified badge is not a reliable signal — every bait listing in this dataset
                carries it.
              </p>
            )}
          </div>

          <div className="card side-card">
            <h3>Record</h3>
            <div className="kv"><span>Listing id</span><span className="mono">{listing.listing_id}</span></div>
            <div className="kv"><span>Posted</span><span>{istDateTime(listing.posted_at)}</span></div>
            <div className="kv"><span>Status</span><span>{listing.is_live ? "Live" : "Not live"}</span></div>
            <div className="kv">
              <span>Coordinates</span>
              <span>{listing.latitude.toFixed(4)}, {listing.longitude.toFixed(4)}</span>
            </div>
            {listing.coordinates_corrected && (
              <p className="muted" style={{ fontSize: 12.5, marginBottom: 0 }}>
                Latitude and longitude arrived swapped and have been put back in order.
              </p>
            )}
          </div>

          {project && (
            <div className="card side-card">
              <h3>Project</h3>
              <div className="kv"><span>Name</span><span>{project.apartment_name}</span></div>
              <div className="kv"><span>Developer</span><span>{project.developer_name}</span></div>
              <div className="kv"><span>Status</span><span>{titleCase(project.project_status)}</span></div>
              <div className="kv">
                <span>Price band</span>
                <span>{inr(project.price_min_inr)} – {inr(project.price_max_inr)}</span>
              </div>
              <div className="kv"><span>Possession</span><span>{project.possession_date}</span></div>
              <div className="kv"><span>RERA</span><span className="mono">{project.rera_number}</span></div>
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}
