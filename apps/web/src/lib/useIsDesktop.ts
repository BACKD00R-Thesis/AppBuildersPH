import { useSyncExternalStore } from 'react'

/** The laptop layout needs about 1180px to fit sidebar, script, preview and style panel. */
export const DESKTOP_QUERY = '(min-width: 1180px)'

function subscribe(onChange: () => void) {
  const mql = window.matchMedia(DESKTOP_QUERY)
  mql.addEventListener('change', onChange)
  return () => mql.removeEventListener('change', onChange)
}

export function useIsDesktop(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(DESKTOP_QUERY).matches,
    () => true,
  )
}
