import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Loads data when the screen gains focus, and keeps polling every `intervalMs`
 * while `shouldPoll(data)` is true (e.g. while a script or render is in progress).
 */
export function useResource<T>(
  load: () => Promise<T>,
  options: { intervalMs?: number; shouldPoll?: (data: T) => boolean } = {},
) {
  const { intervalMs = 1500, shouldPoll } = options;
  const [data, setData] = useState<T | undefined>(undefined);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const loadRef = useRef(load);
  const pollRef = useRef(shouldPoll);
  useEffect(() => {
    loadRef.current = load;
    pollRef.current = shouldPoll;
  });

  const reload = useCallback(async () => {
    try {
      const result = await loadRef.current();
      setData(result);
      setError(null);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      return undefined;
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      let timer: ReturnType<typeof setTimeout> | undefined;
      const tick = async () => {
        const result = await reload();
        if (active && result !== undefined && pollRef.current?.(result)) {
          timer = setTimeout(tick, intervalMs);
        }
      };
      tick();
      return () => {
        active = false;
        if (timer) clearTimeout(timer);
      };
    }, [reload, intervalMs]),
  );

  return { data, setData, error, loading, reload };
}

/** Restart polling when a value flips (e.g. after starting generation from this screen). */
export function usePollWhile(active: boolean, poll: () => unknown, intervalMs = 1500) {
  const pollRef = useRef(poll);
  useEffect(() => {
    pollRef.current = poll;
  });
  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => pollRef.current(), intervalMs);
    return () => clearInterval(id);
  }, [active, intervalMs]);
}
