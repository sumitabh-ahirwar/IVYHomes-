import { useEffect } from "react";
import useApiData from "../components/useApiData.js";
import ListingCard from "../components/ListingCard.jsx";
import { useSession } from "../lib/session.jsx";

export default function Saved() {
  const { savedIds, refreshSaved } = useSession();
  // Re-read on mount so the list is right after a reload or a re-login.
  useEffect(() => {
    refreshSaved();
  }, [refreshSaved]);

  const { data, loading, error } = useApiData(`/api/saved?n=${savedIds.size}`);

  return (
    <main className="page">
      <div className="page-head">
        <h1>Saved listings</h1>
        <p>
          Held against your account on the server, so they are still here after a reload and after
          signing out and back in. Each demo user keeps a separate list.
        </p>
      </div>

      {error && <div className="notice notice-danger">{error}</div>}
      {loading && <div className="spinner">Loading…</div>}

      {!loading && data && data.results.length === 0 && (
        <div className="card empty">
          Nothing saved yet. Tap the heart on any listing to keep it here.
        </div>
      )}

      {!loading && data && data.results.length > 0 && (
        <div className="grid">
          {data.results.map((l) => (
            <ListingCard key={l.listing_id} listing={l} />
          ))}
        </div>
      )}
    </main>
  );
}
