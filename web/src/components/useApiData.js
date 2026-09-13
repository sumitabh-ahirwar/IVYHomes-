import { useEffect, useState } from "react";
import { useSession } from "../lib/session.jsx";

/** Fetch a path whenever it changes, with loading and error state. */
export default function useApiData(path) {
  const { api } = useSession();
  const [state, setState] = useState({ data: null, loading: true, error: null });

  useEffect(() => {
    if (!api || !path) return undefined;
    let live = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    api(path)
      .then((data) => live && setState({ data, loading: false, error: null }))
      .catch((error) => live && setState({ data: null, loading: false, error: error.message }));
    return () => {
      live = false;
    };
  }, [api, path]);

  return state;
}
