import { api } from '../lib/api'
import { cn } from '../lib/cn'
import { speakerOf } from '../lib/speakers'
import type { Speaker } from '../lib/types'

interface Props {
  speaker: Speaker
  /** Diameter in px. */
  size?: number
  /** Used for the initials of a character without art. */
  fontSize?: number
  className?: string
}

/**
 * Head crops of the 4:5 mascot art: zoom (art width / circle width) and vertical position,
 * chosen so the face fills the circle (Bunso's buns sit higher than Tito's hair).
 */
const crops: Record<string, { zoom: string; y: string }> = {
  'tito-boy': { zoom: '150%', y: '1%' },
  bunso: { zoom: '150%', y: '11%' },
}

/** The speaker's face in their color (mascot sheet). Characters without art show initials. */
export function Avatar({ speaker, size = 26, fontSize = 9, className }: Props) {
  const info = speakerOf(speaker)
  const crop = crops[speaker]
  return (
    <span
      aria-hidden
      className={cn(
        'border-mascot-ink text-ink flex shrink-0 items-center justify-center overflow-hidden rounded-full border-[1.5px] bg-no-repeat font-bold whitespace-nowrap',
        info.colorClass,
        className,
      )}
      style={{
        width: size,
        height: size,
        fontSize,
        ...(crop && {
          backgroundImage: `url(${api.characterImageUrl(speaker)})`,
          backgroundSize: crop.zoom,
          backgroundPosition: `50% ${crop.y}`,
        }),
      }}
    >
      {!crop && info.initials}
    </span>
  )
}
