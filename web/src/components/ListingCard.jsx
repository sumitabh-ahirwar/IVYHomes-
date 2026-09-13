import { Link } from "react-router-dom";
import { bhkLabel, inr, perSqft, sqft, titleCase } from "../lib/format.js";
import { useSession } from "../lib/session.jsx";

export default function ListingCard({ listing }) {
  const { savedIds, toggleSaved } = useSession();
  const saved = savedIds.has(listing.listing_id);

  return (
    <article className="card listing-card">
      <div className="lc-head">
        <div>
          <h3>
            <Link to={`/listings/${listing.listing_id}`}>{titleCase(listing.apartment_name)}</Link>
          </h3>
          <div className="lc-loc">
            {titleCase(listing.locality)} · {titleCase(listing.property_type)}
          </div>
        </div>
        <button
          className={`heart ${saved ? "on" : ""}`}
          onClick={() => toggleSaved(listing.listing_id)}
          aria-label={saved ? "Remove from saved" : "Save listing"}
          title={saved ? "Remove from saved" : "Save listing"}
        >
          {saved ? "♥" : "♡"}
        </button>
      </div>

      <div>
        <div className="lc-price">{inr(listing.price)}</div>
        <div className="lc-ppsf">{perSqft(listing.price_per_sqft)}</div>
      </div>

      {(listing.is_fake || listing.is_corrupt || listing.is_duplicate || listing.area_unit_corrected) && (
        <div className="lc-flags">
          {listing.is_fake && <span className="pill pill-danger">Suspected bait</span>}
          {listing.is_corrupt && <span className="pill pill-warn">Impossible data</span>}
          {listing.is_duplicate && <span className="pill">Duplicate</span>}
          {listing.area_unit_corrected && <span className="pill pill-accent">Area converted</span>}
        </div>
      )}

      <div className="lc-specs">
        <span>{bhkLabel(listing.bedroom)}</span>
        <span>{sqft(listing.carpet_area)}</span>
        <span>{titleCase(listing.furnishing)}</span>
      </div>
    </article>
  );
}
