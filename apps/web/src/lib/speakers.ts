import type { Speaker } from './types'

interface SpeakerInfo {
  name: string
  initials: string
  vibe: string
  /** Tailwind background class in the character's color (mascot sheet). */
  colorClass: string
}

const known: Record<string, SpeakerInfo> = {
  'tito-boy': { name: 'Tito', initials: 'T', vibe: 'Warm and patient', colorClass: 'bg-tito' },
  bunso: { name: 'Bunso', initials: 'B', vibe: 'Quick and curious', colorClass: 'bg-bunso' },
}

/** The design's two speakers, in display order. */
export const speakerIds: Speaker[] = ['tito-boy', 'bunso']

/** Display info for a speaker; unknown ids (a custom character manifest) get a plain fallback. */
export function speakerOf(id: Speaker): SpeakerInfo {
  return known[id] ?? { name: id, initials: id.slice(0, 1).toUpperCase(), vibe: '', colorClass: 'bg-mint' }
}
