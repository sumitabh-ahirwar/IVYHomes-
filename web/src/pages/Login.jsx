import { useState } from "react";
import { useSession } from "../lib/session.jsx";

const DEMO_USERS = ["demo1@ivy.homes", "demo2@ivy.homes", "demo3@ivy.homes"];

export default function Login() {
  const { signIn } = useSession();
  const [email, setEmail] = useState("demo1@ivy.homes");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signIn(email.trim(), password);
    } catch (err) {
      setError(err.message || "Could not sign in.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="card login-card">
        <h1>Sign in</h1>
        <p>Mumbai listings, rentals and projects.</p>

        <form className="login-form" onSubmit={onSubmit}>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              className="input"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              className="input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="demo-accounts">
          Demo accounts — they share one password:
          <div style={{ display: "grid", marginTop: 6 }}>
            {DEMO_USERS.map((u) => (
              <button key={u} type="button" onClick={() => setEmail(u)}>
                {u}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
