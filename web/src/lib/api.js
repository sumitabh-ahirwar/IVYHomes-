/**
 * Client-side API access and session handling.
 *
 * The access token upstream issues lives for 15 minutes, not the 24 hours the
 * reference claims, so a session only survives a working day if the client
 * refreshes it. Tokens are kept in localStorage so a page reload keeps you
 * signed in, and every request refreshes proactively when the token is close to
 * expiry and reactively on a 401.
 */

const STORE_KEY = "ivy.session";

export function loadSession() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveSession(session) {
  try {
    if (session) localStorage.setItem(STORE_KEY, JSON.stringify(session));
    else localStorage.removeItem(STORE_KEY);
  } catch {
    /* private browsing - the session simply will not survive a reload */
  }
}

function withExpiry(payload) {
  return {
    access_token: payload.access_token,
    refresh_token: payload.refresh_token,
    user: payload.user,
    // Renew a minute early so a request never races the expiry.
    expires_at: Date.now() + (payload.expires_in || 900) * 1000,
  };
}

async function request(path, { method = "GET", body, token } = {}) {
  const res = await fetch(path, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!res.ok) {
    const err = new Error(data?.detail || `request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return data;
}

export async function login(email, password) {
  return withExpiry(await request("/api/auth/login", { method: "POST", body: { email, password } }));
}

export async function refreshSession(session) {
  const next = await request("/api/auth/refresh", {
    method: "POST",
    body: { refresh_token: session.refresh_token },
  });
  return withExpiry({ ...next, user: next.user || session.user });
}

/**
 * Build a fetcher bound to the current session. `onSession` is called whenever
 * the token is renewed so the app can persist it.
 */
export function createClient(session, onSession) {
  let current = session;

  async function ensureFresh() {
    if (!current) throw new Error("not signed in");
    if (Date.now() < current.expires_at - 60_000) return current;
    current = await refreshSession(current);
    onSession(current);
    return current;
  }

  return async function apiFetch(path, opts = {}) {
    const s = await ensureFresh();
    try {
      return await request(path, { ...opts, token: s.access_token });
    } catch (err) {
      if (err.status !== 401) throw err;
      // Token rejected sooner than expected - renew once and retry.
      current = await refreshSession(current);
      onSession(current);
      return request(path, { ...opts, token: current.access_token });
    }
  };
}

export function qs(params) {
  const u = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "" && v !== false) u.set(k, v);
  }
  const s = u.toString();
  return s ? `?${s}` : "";
}
