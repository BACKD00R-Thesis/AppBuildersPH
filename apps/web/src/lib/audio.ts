/** One shared audio player for line previews and voice samples: starting one stops the other. */
import { useSyncExternalStore } from 'react'

let element: HTMLAudioElement | null = null
let playingKey: string | null = null
const listeners = new Set<() => void>()

function setPlaying(key: string | null) {
  playingKey = key
  listeners.forEach((listener) => listener())
}

function audio(): HTMLAudioElement {
  if (!element) {
    element = new Audio()
    element.addEventListener('ended', () => setPlaying(null))
    element.addEventListener('error', () => setPlaying(null))
  }
  return element
}

/** Play `url`, tagged with `key` (a line id or "sample:<speaker>") so the UI can show what's playing. */
export async function play(key: string, url: string): Promise<void> {
  const el = audio()
  el.pause()
  el.src = url
  setPlaying(key)
  try {
    await el.play()
  } catch (err) {
    setPlaying(null)
    throw err
  }
}

export function stop(): void {
  element?.pause()
  setPlaying(null)
}

/** The key of the clip that's playing, or null. */
export function usePlaying(): string | null {
  return useSyncExternalStore(
    (onChange) => {
      listeners.add(onChange)
      return () => listeners.delete(onChange)
    },
    () => playingKey,
    () => null,
  )
}
