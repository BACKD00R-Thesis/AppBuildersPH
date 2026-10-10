/** A character id from the engine's assets/characters/manifest.json. The design has two. */
export type Speaker = 'tito-boy' | 'bunso' | (string & {})

/** A background id from assets/backgrounds/manifest.json (parkour, kart, blocks, soap). */
export type BackgroundId = string

export type CaptionStyle = 'bold-pop' | 'clean' | 'outline'

/** quick: Kokoro/Piper, fast on any laptop. expressive: Chatterbox, acted, optional (NVIDIA GPU). */
export type VoiceStyle = 'quick' | 'expressive'

export type VideoLength = 30 | 60 | 90

export type StepStatus = 'done' | 'current' | 'pending'

export interface ScriptLine {
  /** Server id, or a temporary "new-…" id until the line is saved. */
  id: string
  speaker: Speaker
  text: string
  /** Spoken length of this line in seconds (estimated until it has been voiced). */
  seconds: number
}

/** A video as shown in lists, thumbnails and the player header. */
export interface Video {
  id: string
  title: string
  /** Subject label, e.g. "Biology". */
  subject: string
  durationSec: number
  /** Two-line caption for thumbnails: white line, then mustard line. */
  caption: [string, string]
  lineCount: number
  background: BackgroundId
  isNew: boolean
  /** Where tapping the video goes: its current step. */
  href: string
  /** Short state for in-progress videos ("Writing the script"), or null when the video is ready. */
  progressLabel: string | null
  hasVideo: boolean
  /** When the finished video was rendered (ISO time), or null. */
  madeAt: string | null
}

export interface Step {
  id: string
  status: StepStatus
}

export interface NewVideoDraft {
  file: File | null
  notes: string
  lengthSec: VideoLength
  taglish: boolean
}
