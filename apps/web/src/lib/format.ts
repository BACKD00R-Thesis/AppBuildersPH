/** 21 -> "0:21", 72 -> "1:12" */
export function clock(totalSeconds: number): string {
  const s = Math.max(0, Math.round(totalSeconds))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

/** First word of each caption line, for the tiny list thumbnail. */
export function shortCaption(caption: [string, string]): [string, string] {
  const first = (s: string) => s.split(' ')[0].replace(/[^\p{L}\p{N}’']/gu, '')
  return [first(caption[0]), first(caption[1])]
}

/**
 * A thumbnail caption from any text, in the video's style: up to two words on the
 * white line, the next word on the mustard line. "Cellular respiration" -> ["CELLULAR", "RESPIRATION"].
 */
export function captionFromText(text: string): [string, string] {
  const words = text.replace(/_+/g, ' ').trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return ['', '']
  if (words.length === 1) return ['', words[0]]
  const first = words.slice(0, Math.min(2, words.length - 1))
  return [first.join(' '), words[first.length]]
}

/** "Week6_Respiration.pdf, 3.1 MB" style size label. */
export function fileSize(bytes: number): string {
  return bytes >= 1_048_576 ? `${(bytes / 1_048_576).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`
}
