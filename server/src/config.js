/**
 * Configuration. The API key is a server-side secret: it never reaches the
 * browser. Values can be overridden by environment variables for deployment.
 */
export const BASE_URL = process.env.IVY_BASE_URL || "https://solve.ivy.homes";
export const API_KEY = process.env.IVY_API_KEY || "IVY26-0D2F818EE4B7";

// Service account used only to warm the dataset cache. End users log in with
// their own credentials; their tokens are never used for cache fills.
export const SERVICE_EMAIL = process.env.IVY_SERVICE_EMAIL || "demo1@ivy.homes";
export const SERVICE_PASSWORD = process.env.IVY_SERVICE_PASSWORD || "8adfaaa62a";

export const PORT = process.env.PORT || 8787;

// The reference moment the assignment anchors every figure to.
export const REFERENCE_ISO = "2026-09-10T00:00:00+05:30";

// Dataset cache lifetime. A full refresh is ~156 upstream requests; the key's
// budget is 1200/min, so this is nowhere near the limit.
export const CACHE_TTL_MS = Number(process.env.CACHE_TTL_MS || 15 * 60 * 1000);
