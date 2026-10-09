/** Fixed choices offered in the UI. They match what the engine accepts. */
import type { CaptionStyle, VideoLength } from './types'

export const captionStyles: { value: CaptionStyle; label: string }[] = [
  { value: 'bold-pop', label: 'Bold pop' },
  { value: 'clean', label: 'Clean' },
  { value: 'outline', label: 'Outline' },
]

export const videoLengths: { value: VideoLength; label: string }[] = [
  { value: 30, label: '30s' },
  { value: 60, label: '60s' },
  { value: 90, label: '90s' },
]

/** Same plan as the engine (server/app/pipeline/script.py, LENGTH_PLANS). */
export const keyIdeasForLength: Record<VideoLength, number> = { 30: 3, 60: 5, 90: 8 }

/** Rough time the local model takes to write a script, for "About N seconds left". */
export const scriptSecondsForLength: Record<VideoLength, number> = { 30: 35, 60: 50, 90: 70 }

/** Shown until the engine's background list has loaded, and for unknown ids. */
export const fallbackBackground = { name: 'Background', shortName: 'Background', from: '#3b4a2e', to: '#151a14' }
