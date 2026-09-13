import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import useApiData from "../components/useApiData.js";
import { inr, inrExact, perSqft, titleCase } from "../lib/format.js";

const AXIS = { fontSize: 11, fill: "#64748b" };
const GRID = "rgba(126,158,214,0.1)";
const CYAN = "#22d3ee";
const INDIGO = "#818cf8";
const ROSE = "#fb7185";

function Stat({ label, value, note }) {
  return (
    <div className="card stat">
      <div className="s-label">{label}</div>
      <div className="s-value">{value}</div>
      {note && <div className="s-note">{note}</div>}
    </div>
  );
}

export default function Insights() {
  const { data, loading, error } = useApiData("/api/insights");

  if (loading) return <main className="page spinner">Crunching the dataset…</main>;
  if (error) return <main className="page"><div className="notice notice-danger">{error}</div></main>;

  const { integrity, rentals, projects, activity } = data;
  const pctTrusted = ((integrity.trusted / integrity.total_records) * 100).toFixed(1);

  const localityChart = data.by_locality.map((l) => ({
    name: titleCase(l.locality).replace(" West", " W").replace(" East", " E"),
    ppsf: l.median_price_per_sqft,
  }));
  const bhkChart = data.by_bhk
    .filter((b) => b.bedroom > 0)
    .map((b) => ({ name: `${b.bedroom} BHK`, price: b.median_price, count: b.count }));
  const corruption = Object.entries(integrity.corruption_breakdown).map(([k, v]) => ({ reason: k, count: v }));

  return (
    <main className="page">
      <div className="page-head">
        <h1>Market insights</h1>
        <p>
          The documented <code>/v1/analytics/summary</code> endpoint does not exist, so everything
          here is computed from the full record set after correcting the units and removing the
          records that should not count. The second half is what this dataset gets wrong — the part
          that changes whether you should believe a price.
        </p>
      </div>

      <div className="stat-row">
        <Stat label="Listing records" value={integrity.total_records.toLocaleString("en-IN")}
              note={`${integrity.distinct_properties.toLocaleString("en-IN")} distinct properties`} />
        <Stat label="Live listings" value={integrity.live.toLocaleString("en-IN")}
              note={`${integrity.not_live.toLocaleString("en-IN")} returned but not live`} />
        <Stat label="Median price" value={inr(data.median_price)} note="live, genuine listings only" />
        <Stat label="Median rate" value={perSqft(data.median_price_per_sqft)} note="on carpet area" />
        <Stat label="Trustworthy records" value={`${pctTrusted}%`}
              note={`${integrity.trusted.toLocaleString("en-IN")} of ${integrity.total_records.toLocaleString("en-IN")}`} />
      </div>

      <div className="two-col">
        <section className="card panel">
          <h2>Rate by locality</h2>
          <p className="panel-sub">Median rupees per square foot of carpet area.</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={localityChart} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
              <defs>
                <linearGradient id="gCyan" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={CYAN} stopOpacity={0.95} />
                  <stop offset="100%" stopColor={INDIGO} stopOpacity={0.5} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="2 5" stroke={GRID} vertical={false} />
              <XAxis dataKey="name" tick={AXIS} interval={0} angle={-35} textAnchor="end" height={62} />
              <YAxis tick={AXIS} tickFormatter={(v) => `${Math.round(v / 1000)}k`} width={42} />
              <Tooltip formatter={(v) => perSqft(v)} cursor={{ fill: "rgba(126,158,214,0.07)" }} />
              <Bar dataKey="ppsf" fill="url(#gCyan)" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>

        <section className="card panel">
          <h2>Median price by size</h2>
          <p className="panel-sub">Live, genuine listings only.</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={bhkChart} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
              <defs>
                <linearGradient id="gCyan" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={CYAN} stopOpacity={0.95} />
                  <stop offset="100%" stopColor={INDIGO} stopOpacity={0.5} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="2 5" stroke={GRID} vertical={false} />
              <XAxis dataKey="name" tick={AXIS} />
              <YAxis tick={AXIS} tickFormatter={(v) => `${(v / 1e7).toFixed(1)}Cr`} width={46} />
              <Tooltip formatter={(v, n) => (n === "price" ? inr(v) : v)} cursor={{ fill: "rgba(126,158,214,0.07)" }} />
              <Bar dataKey="price" fill="url(#gCyan)" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>
      </div>

      <section className="card panel">
        <h2>Listings posted per day</h2>
        <p className="panel-sub">
          Grouped by IST calendar day, which is the boundary the API itself uses.{" "}
          <strong>{activity.listings_last_7_days}</strong> listings were posted in the seven days
          before the reference moment.
        </p>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={activity.timeline} margin={{ top: 4, right: 10, bottom: 4, left: 4 }}>
            <defs>
              <linearGradient id="gArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={CYAN} stopOpacity={0.45} />
                <stop offset="100%" stopColor={CYAN} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="2 5" stroke={GRID} vertical={false} />
            <XAxis dataKey="date" tick={AXIS} minTickGap={48} />
            <YAxis tick={AXIS} width={32} />
            <Tooltip cursor={{ stroke: CYAN, strokeOpacity: 0.35 }} />
            <Area type="monotone" dataKey="count" stroke={CYAN} strokeWidth={2} fill="url(#gArea)" />
          </AreaChart>
        </ResponsiveContainer>
      </section>

      <section className="card panel">
        <h2>What this dataset gets wrong</h2>
        <p className="panel-sub">
          Each figure below is applied to what you see elsewhere in the app — corrupt, bait and
          repeat records are filtered out of browsing by default, and converted values are labelled
          wherever they appear.
        </p>

        <div className="stat-row" style={{ marginBottom: 14 }}>
          <Stat label="Suspected bait" value={integrity.fake}
                note={`${integrity.fake_operations.length} phone numbers`} />
          <Stat label="Impossible records" value={integrity.corrupt} note="cannot describe a real home" />
          <Stat label="Repeat postings" value={integrity.duplicate_records}
                note={`${integrity.duplicate_clusters} properties listed twice or more`} />
          <Stat label="Areas converted" value={integrity.area_unit_corrected} note="published in m², not ft²" />
          <Stat label="Coordinates fixed" value={integrity.coordinates_corrected} note="lat/long swapped" />
        </div>

        <div className="two-col">
          <div>
            <h3 style={{ fontSize: 14, margin: "0 0 8px" }}>Why records are impossible</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={corruption} layout="vertical" margin={{ left: 4, right: 20 }}>
                <defs>
                  <linearGradient id="gRose" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor={ROSE} stopOpacity={0.9} />
                    <stop offset="100%" stopColor="#c084fc" stopOpacity={0.7} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 5" stroke={GRID} horizontal={false} />
                <XAxis type="number" tick={AXIS} />
                <YAxis type="category" dataKey="reason" tick={{ fontSize: 10, fill: "#64748b" }} width={168} />
                <Tooltip cursor={{ fill: "rgba(126,158,214,0.07)" }} />
                <Bar dataKey="count" radius={[0, 5, 5, 0]}>
                  {corruption.map((_, i) => <Cell key={i} fill="url(#gRose)" />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div>
            <h3 style={{ fontSize: 14, margin: "0 0 8px" }}>The lead-generation operation</h3>
            <p className="muted" style={{ fontSize: 13, marginTop: 0 }}>
              Five phone numbers, each carrying exactly {integrity.fake_operations[0]?.listings} listings
              under several different agent names, every one of them marked live and verified, and
              priced at roughly half the going rate.
            </p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Phone</th>
                    <th className="num">Listings</th>
                    <th className="num">Names used</th>
                    <th className="num">Median ₹/sq ft</th>
                  </tr>
                </thead>
                <tbody>
                  {integrity.fake_operations.map((op) => (
                    <tr key={op.phone}>
                      <td className="mono">{op.phone}</td>
                      <td className="num">{op.listings}</td>
                      <td className="num" title={op.identities.join(", ")}>{op.identities.length}</td>
                      <td className="num">{op.median_price_per_sqft.toLocaleString("en-IN")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <div className="two-col">
        <section className="card panel">
          <h2>Rentals</h2>
          <div className="kv"><span>Rental records</span><span>{rentals.total.toLocaleString("en-IN")}</span></div>
          <div className="kv"><span>Live</span><span>{rentals.live.toLocaleString("en-IN")}</span></div>
          <div className="kv"><span>Median rent</span><span>{inrExact(rentals.median_rent)}</span></div>
          <div className="kv">
            <span>Deposits republished in rupees</span>
            <span>{rentals.deposit_unit_corrected}</span>
          </div>
          <div className="kv">
            <span>Titles naming the wrong locality</span>
            <span>{rentals.title_locality_mismatch.toLocaleString("en-IN")}</span>
          </div>
          <p className="muted" style={{ fontSize: 13, marginBottom: 0 }}>
            The <code>title</code> on a rental names a locality picked at random and disagrees with
            the record's own <code>locality</code> field nine times out of ten. Every locality filter
            and figure in this app uses the field, not the title.
          </p>
        </section>

        <section className="card panel">
          <h2>Projects</h2>
          <div className="kv"><span>Projects</span><span>{projects.total}</span></div>
          <div className="kv">
            <span>Reporting a wrong listing count</span>
            <span>{projects.listing_count_wrong} of {projects.total}</span>
          </div>
          <div className="kv">
            <span>Minimum price given in lakhs</span>
            <span>{projects.price_min_unit_corrected}</span>
          </div>
          <h3 style={{ fontSize: 13, margin: "14px 0 6px", color: "#6b6963" }}>Costliest projects</h3>
          <div className="mini-list">
            {projects.costliest.map((p) => (
              <div className="mini" key={p.project_id}>
                <span>{p.apartment_name} <span className="faint">· {titleCase(p.locality)}</span></span>
                <span>{inr(p.price_max_inr)}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
