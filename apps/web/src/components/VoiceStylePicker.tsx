import { cn } from '../lib/cn'
import { voiceStyles } from '../lib/options'
import { useStore } from '../lib/store'
import type { VoiceStyle } from '../lib/types'

interface Props {
  value: VoiceStyle
  onChange: (style: VoiceStyle) => void
  className?: string
}

/**
 * Quick or Expressive voices, saved per video. Expressive is optional: on a laptop without
 * the voice pack or an NVIDIA graphics card it's greyed out, with the engine's reason.
 */
export function VoiceStylePicker({ value, onChange, className }: Props) {
  const { health } = useStore()
  const expressive = health?.expressive
  return (
    <div role="radiogroup" aria-label="Voice style" className={cn('flex w-full flex-col gap-2', className)}>
      {voiceStyles.map((style) => {
        const unavailable = style.value === 'expressive' && !expressive?.ok
        const selected = value === style.value
        return (
          <button
            key={style.value}
            type="button"
            role="radio"
            aria-checked={selected}
            disabled={unavailable}
            onClick={() => onChange(style.value)}
            className={cn(
              'rounded-input flex w-full items-start gap-3 border-[1.5px] p-3 text-left',
              selected ? 'border-green-2 bg-mint' : 'border-mint-line bg-card',
              unavailable && 'cursor-not-allowed opacity-60',
            )}
          >
            <span
              aria-hidden
              className={cn(
                'mt-[3px] flex size-4 shrink-0 items-center justify-center rounded-full border-[1.5px]',
                selected ? 'border-green-2' : 'border-muted',
              )}
            >
              {selected && <span className="bg-green-2 size-2 rounded-full" />}
            </span>
            <span className="flex min-w-0 flex-col gap-[2px]">
              <span className="text-ink text-[14px] font-semibold">{style.label}</span>
              <span className="text-muted text-[12px] leading-snug">{style.description}</span>
              {unavailable && (
                <span className="text-clay-deep text-[12px] leading-snug">
                  Not available on this laptop{expressive ? `: ${expressive.detail}` : ''}.
                </span>
              )}
            </span>
          </button>
        )
      })}
    </div>
  )
}
