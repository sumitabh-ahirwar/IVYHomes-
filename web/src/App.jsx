import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useSession } from "./lib/session.jsx";
import Login from "./pages/Login.jsx";
import Listings from "./pages/Listings.jsx";
import ListingDetail from "./pages/ListingDetail.jsx";
import Saved from "./pages/Saved.jsx";
import Rentals from "./pages/Rentals.jsx";
import Projects from "./pages/Projects.jsx";
import Insights from "./pages/Insights.jsx";

const NAV = [
  { to: "/listings", label: "Buy" },
  { to: "/rentals", label: "Rent" },
  { to: "/projects", label: "Projects" },
  { to: "/saved", label: "Saved" },
  { to: "/insights", label: "Insights" },
];

export default function App() {
  const { session, signOut, savedIds } = useSession();

  if (!session) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          Ivy Homes <span>Mumbai</span>
        </div>
        <nav className="nav">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} className={({ isActive }) => (isActive ? "active" : "")}>
              {n.label}
              {n.to === "/saved" && savedIds.size > 0 ? ` (${savedIds.size})` : ""}
            </NavLink>
          ))}
        </nav>
        <div className="topbar-right">
          <span>{session.user?.email}</span>
          <button className="btn btn-ghost btn-sm" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<Navigate to="/listings" replace />} />
        <Route path="/login" element={<Navigate to="/listings" replace />} />
        <Route path="/listings" element={<Listings />} />
        <Route path="/listings/:id" element={<ListingDetail />} />
        <Route path="/rentals" element={<Rentals />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/saved" element={<Saved />} />
        <Route path="/insights" element={<Insights />} />
        <Route path="*" element={<div className="page empty">Page not found.</div>} />
      </Routes>
    </div>
  );
}
