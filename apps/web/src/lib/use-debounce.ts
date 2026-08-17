import { useState, useEffect } from "react";

/**
 * Debounces a rapidly-changing value. Returns the debounced value after
 * the specified delay (ms) of inactivity.
 */
export function useDebounce<T>(value: T, delay = 500): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
