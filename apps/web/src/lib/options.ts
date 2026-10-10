/** Fixed choices offered in the UI. They match what the engine accepts. */
import type { CaptionStyle, VideoLength, VoiceStyle } from './types'

export const captionStyles: { value: CaptionStyle; label: string }[] = [
  { value: 'bold-pop', label: 'Bold pop' },
  { value: 'clean', label: 'Clean' },
  { value: 'outline', label: 'Outline' },
]

/** The two voice styles, in the words users see. Expressive needs the optional voice pack. */
export const voiceStyles: { value: VoiceStyle; label: string; description: string }[] = [
  { value: 'quick', label: 'Quick', description: 'Clear, steady voices. Fast on any laptop.' },
  {
    value: 'expressive',
    label: 'Expressive',
    description: 'Voices that act it out: laughs, excitement, a bored sigh. Slower; needs an NVIDIA graphics card.',
  },
]

export const videoLengths: { value: VideoLength; label: string }[] = [
  { value: 30, label: '30s' },
  { value: 60, label: '60s' },
  { value: 90, label: '90s' },
]

/**
 * Taglish mode is parked for now: the TTS engines have no Tagalog voice and mispronounce Filipino
 * words. While false, new videos are English and the toggle is hidden. The engine still supports it.
 */
export const TAGLISH_ENABLED = false

/** Same plan as the engine (server/app/pipeline/script.py, LENGTH_PLANS). */
export const keyIdeasForLength: Record<VideoLength, number> = { 30: 3, 60: 5, 90: 8 }

/** Rough time the local model takes to write a script, for "About N seconds left". */
export const scriptSecondsForLength: Record<VideoLength, number> = { 30: 35, 60: 50, 90: 70 }

/** Shown until the engine's background list has loaded, and for unknown ids. */
export const fallbackBackground = { name: 'Background', shortName: 'Background', from: '#3b4a2e', to: '#151a14' }
