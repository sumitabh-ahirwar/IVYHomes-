/** Money and area formatting, in the units Indian property is actually quoted in. */

export function inr(value) {
  if (value === null || value === undefined) return "—";
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  const abs = Math.abs(n);
  if (abs >= 1e7) return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (abs >= 1e5) return `₹${(n / 1e5).toFixed(2)} L`;
  return `₹${n.toLocaleString("en-IN")}`;
}

export function inrExact(value) {
  if (value === null || value === undefined) return "—";
  return `₹${Number(value).toLocaleString("en-IN")}`;
}

export function sqft(value) {
  if (value === null || value === undefined) return "—";
  return `${Number(value).toLocaleString("en-IN")} sq ft`;
}

export function perSqft(value) {
  if (!value) return "—";
  return `₹${Number(value).toLocaleString("en-IN")}/sq ft`;
}

/** The dataset's day boundaries are IST, so dates are rendered in IST. */
export function istDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function istDay(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function titleCase(s) {
  return String(s || "")
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function bhkLabel(n) {
  return n === 0 ? "Plot" : `${n} BHK`;
}
