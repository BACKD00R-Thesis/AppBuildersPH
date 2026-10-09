import { cn } from '../lib/cn'
import { speakerOf } from '../lib/speakers'
import type { Speaker } from '../lib/types'

interface Props {
  speaker: Speaker
  /** Diameter in px. */
  size?: number
  fontSize?: number
  className?: string
}

/** Figma: Avatar/TB (light, outlined) and Avatar/B (solid green). */
export function Avatar({ speaker, size = 26, fontSize = 9, className }: Props) {
  return (
    <span
      aria-hidden
      className={cn(
        'flex shrink-0 items-center justify-center rounded-full font-bold whitespace-nowrap',
        speaker === 'tito-boy' ? 'border-[1.5px] border-mint-line bg-card text-green' : 'bg-green text-page',
        className,
      )}
      style={{ width: size, height: size, fontSize }}
    >
      {speakerOf(speaker).initials}
    </span>
  )
}
