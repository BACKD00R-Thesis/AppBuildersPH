import type { Speaker } from './types'

const known: Record<string, { name: string; initials: string; vibe: string }> = {
  'tito-boy': { name: 'Tito Boy', initials: 'TB', vibe: 'Loud and slow' },
  bunso: { name: 'Bunso', initials: 'B', vibe: 'Fast and smug' },
}

/** The design's two speakers, in display order. */
export const speakerIds: Speaker[] = ['tito-boy', 'bunso']

/** Display info for a speaker; unknown ids (a custom character manifest) get a plain fallback. */
export function speakerOf(id: Speaker): { name: string; initials: string; vibe: string } {
  return known[id] ?? { name: id, initials: id.slice(0, 1).toUpperCase(), vibe: '' }
}
