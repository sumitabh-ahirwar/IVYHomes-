/**
 * Thin client for the Ivy Homes API.
 *
 * Encodes three things the published reference gets wrong:
 *   1. the key travels in an `X-API-Key` header, not a `?api_key=` query param;
 *   2. collections page with `limit`/`offset` (max limit 50), not `page`;
 *   3. `total` under-reports, so the only honest stop condition is `has_more`.
 */
import { BASE_URL, API_KEY } from "./config.js";

export const MAX_LIMIT = 50; // server clamps anything larger down to this

function url(path, params) {
  const u = new URL(path, BASE_URL);
  for (const [k, v] of Object.entries(params || {})) {
    if (v !== undefined && v !== null && v !== "") u.searchParams.set(k, v);
  }
  return u.toString();
}

export async function call(path, { params, method = "GET", token, body } = {}) {
  const headers = { "X-API-Key": API_KEY };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body) headers["Content-Type"] = "application/json";

  const res = await fetch(url(path, params), {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  let data;
  try { data = text ? JSON.parse(text) : null; } catch { data = { detail: text }; }

  if (!res.ok) {
    const err = new Error(detailOf(data) || `upstream ${res.status}`);
    err.status = res.status;
    err.body = data;
    throw err;
  }
  return data;
}

function detailOf(data) {
  const d = data && data.detail;
  if (!d) return null;
  if (typeof d === "string") return d;
  // FastAPI validation errors arrive as an array of objects.
  if (Array.isArray(d)) return d.map((e) => `${(e.loc || []).join(".")}: ${e.msg}`).join("; ");
  return JSON.stringify(d);
}

export async function login(email, password) {
  return call("/auth/login", { method: "POST", body: { email, password } });
}

export async function refresh(refresh_token) {
  return call("/auth/refresh", { method: "POST", body: { refresh_token } });
}

/**
 * Page a collection to its true end.
 *
 * `total` is not trustworthy (it reports roughly 94.5% of the real count) and
 * an offset past `total` still returns rows, so we drive purely off `has_more`
 * and the number of rows actually handed back.
 */
export async function fetchAll(path, { token, params } = {}) {
  const rows = [];
  let offset = 0;
  for (let guard = 0; guard < 1000; guard++) {
    const page = await call(path, {
      token,
      params: { ...params, limit: MAX_LIMIT, offset },
    });
    const batch = page.results || [];
    rows.push(...batch);
    if (!batch.length || !page.has_more) break;
    offset += batch.length;
  }
  return rows;
}
