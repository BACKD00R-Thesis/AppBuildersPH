import type { ReactNode } from 'react'
import { cn } from '../lib/cn'
import { useStore } from '../lib/store'
import type { BackgroundId } from '../lib/types'
import { Avatar } from './Avatar'

interface Props {
  background: BackgroundId
  /** White line, then mustard line (the single highlight). */
  caption: [string, string]
  /** Font size of the first line in px. The second line is 1.25x. */
  captionSize: number
  /** Outline thickness in px. Defaults to captionSize / 8, as in Figma. */
  strokeWidth?: number
  /** Where the caption starts, as a share of the frame height. */
  captionTop?: string
  /**
   * Design width of the frame in px. When set, the caption scales with the frame's actual width
   * (container query units) instead of staying at a fixed px size. Use it for frames that resize.
   */
  fluidWidth?: number
  /** Shows the two speaker avatars in the bottom corners. */
  avatars?: { size: number; fontSize: number }
  /** Size and corner radius go here. */
  className?: string
  children?: ReactNode
}

/**
 * The 9:16 video preview: gradient background, "floor" band, two-line caption. The engine renders
 * the same gradient and band when a background has no gameplay clip, so the preview matches.
 * This is the only place the brainrot look (Archivo Black, outlined, mustard) is allowed.
 */
export function VideoFrame({
  background,
  caption,
  captionSize,
  strokeWidth = captionSize / 8,
  captionTop = '40%',
  fluidWidth,
  avatars,
  className,
  children,
}: Props) {
  const bg = useStore().background(background)
  const size = (px: number) => (fluidWidth ? `${(px / fluidWidth) * 100}cqw` : `${px}px`)
  // Figma uses an OUTSIDE stroke. CSS strokes are centered, so double it and paint the fill on top.
  const outline = { WebkitTextStroke: `${size(strokeWidth * 2)} var(--color-video)`, paintOrder: 'stroke fill' as const }

  return (
    <div
      className={cn('relative shrink-0 overflow-clip', className)}
      style={{
        backgroundImage: `linear-gradient(to bottom, ${bg.from}, ${bg.to})`,
        containerType: fluidWidth ? 'inline-size' : undefined,
      }}
    >
      <div className="absolute inset-x-0 top-[64%] bottom-0 bg-white/5" />
      <div
        className="font-caption absolute left-1/2 flex -translate-x-1/2 flex-col items-center text-center whitespace-nowrap uppercase"
        style={{ top: captionTop }}
      >
        <p className="text-white" style={{ fontSize: size(captionSize), ...outline }}>
          {caption[0]}
        </p>
        <p className="text-mustard" style={{ fontSize: size(captionSize * 1.25), ...outline }}>
          {caption[1]}
        </p>
      </div>
      {avatars && (
        <>
          <Avatar speaker="tito-boy" {...avatars} className="absolute bottom-4 left-[14px]" />
          <Avatar speaker="bunso" {...avatars} className="absolute right-[14px] bottom-4" />
        </>
      )}
      {children}
    </div>
  )
}
