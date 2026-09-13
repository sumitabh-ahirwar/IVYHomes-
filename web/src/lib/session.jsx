import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { createClient, loadSession, login as doLogin, saveSession } from "./api.js";

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [session, setSession] = useState(() => loadSession());
  const [savedIds, setSavedIds] = useState(() => new Set());
  const sessionRef = useRef(session);
  sessionRef.current = session;

  const persist = useCallback((next) => {
    sessionRef.current = next;
    setSession(next);
    saveSession(next);
  }, []);

  const api = useMemo(() => (session ? createClient(session, persist) : null), [session, persist]);

  const signIn = useCallback(
    async (email, password) => {
      persist(await doLogin(email, password));
    },
    [persist]
  );

  const signOut = useCallback(async () => {
    const s = sessionRef.current;
    if (s) {
      // Best effort - upstream keeps the token valid regardless, so discarding
      // it on this side is what actually ends the session.
      fetch("/api/auth/logout", {
        method: "POST",
        headers: { Authorization: `Bearer ${s.access_token}` },
      }).catch(() => {});
    }
    setSavedIds(new Set());
    persist(null);
  }, [persist]);

  /* Saved listings are held upstream per user, so they survive a reload and a
     re-login. We mirror just the ids here to keep the heart icons instant. */
  const refreshSaved = useCallback(async () => {
    if (!api) return;
    try {
      const data = await api("/api/saved");
      setSavedIds(new Set((data.results || []).map((r) => r.listing_id)));
    } catch {
      /* leave the mirror as it is */
    }
  }, [api]);

  useEffect(() => {
    refreshSaved();
  }, [refreshSaved]);

  const toggleSaved = useCallback(
    async (listingId) => {
      if (!api) return;
      const isSaved = savedIds.has(listingId);
      // Optimistic, then reconciled against the server's own list.
      setSavedIds((prev) => {
        const next = new Set(prev);
        if (isSaved) next.delete(listingId);
        else next.add(listingId);
        return next;
      });
      try {
        if (isSaved) await api(`/api/saved/${encodeURIComponent(listingId)}`, { method: "DELETE" });
        else await api("/api/saved", { method: "POST", body: { listing_id: listingId } });
      } finally {
        refreshSaved();
      }
    },
    [api, savedIds, refreshSaved]
  );

  /* Keep the token alive while the tab is open, so the app still works half an
     hour after signing in even if the user has not clicked anything. */
  useEffect(() => {
    if (!api) return undefined;
    const timer = setInterval(() => {
      api("/api/health").catch(() => {});
    }, 5 * 60 * 1000);
    return () => clearInterval(timer);
  }, [api]);

  const value = useMemo(
    () => ({ session, api, signIn, signOut, savedIds, toggleSaved, refreshSaved }),
    [session, api, signIn, signOut, savedIds, toggleSaved, refreshSaved]
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used inside SessionProvider");
  return ctx;
}
