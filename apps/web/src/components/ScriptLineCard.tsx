import { useEffect, useRef } from 'react'
import { cn } from '../lib/cn'
import { clock } from '../lib/format'
import { speakerOf } from '../lib/speakers'
import type { ScriptLine } from '../lib/types'
import { Avatar } from './Avatar'
import { Icon } from './Icon'

export type LineState = 'idle' | 'playing' | 'editing'

interface Props {
  line: ScriptLine
  state: LineState
  density: 'desktop' | 'mobile'
  /** Shown beside "Done" while editing: "Enter to save" on laptop, "Tap play to hear it" on mobile. */
  editHint: string
  /** The line's voice is being generated. */
  loading?: boolean
  onPlay: () => void
  onEdit: () => void
  onChange: (text: string) => void
  onDone: () => void
}

/**
 * Figma: v2/Line/<speaker>/<idle|playing|editing>.
 * Tito Boy sits on mint with no shadow, Bunso on a white card with a shadow.
 * Editing swaps both for a white card with a 2px green border.
 */
export function ScriptLineCard({ line, state, density, editHint, loading, onPlay, onEdit, onChange, onDone }: Props) {
  const desktop = density === 'desktop'
  const titoBoy = line.speaker === 'tito-boy'
  const editing = state === 'editing'
  const speaker = speakerOf(line.speaker)
  const textRef = useRef<HTMLTextAreaElement>(null)

  // Grow the textarea with its content and put the caret at the end when editing starts.
  useEffect(() => {
    const el = textRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [editing, line.text])

  useEffect(() => {
    const el = textRef.current
    if (!editing || !el) return
    el.focus()
    el.setSelectionRange(el.value.length, el.value.length)
  }, [editing])

  return (
    <article
      className={cn(
        'rounded-card flex w-full shrink-0 flex-col gap-2 py-[14px]',
        desktop ? 'px-[18px]' : 'px-4',
        editing
          ? 'border-green bg-card border-2'
          : titoBoy
            ? 'bg-mint'
            : cn('bg-card', desktop ? 'shadow-card' : 'shadow-card-sm'),
      )}
    >
      <header className="flex w-full items-center justify-between">
        <div className="flex items-center gap-2">
          <Avatar speaker={line.speaker} />
          <span className="eyebrow text-green-2">{speaker.name}</span>
        </div>
        <button
          type="button"
          onClick={onPlay}
          aria-label={state === 'playing' ? `Stop ${speaker.name}’s line` : `Play ${speaker.name}’s line`}
          aria-pressed={state === 'playing'}
          aria-busy={loading}
          disabled={loading}
          className={cn(
            'flex shrink-0 items-center justify-center rounded-full',
            desktop ? 'size-[30px]' : 'size-8',
            titoBoy ? 'bg-card' : 'bg-mint',
            loading && 'animate-pulse',
          )}
        >
          <Icon name="play13" />
        </button>
      </header>

      {editing ? (
        <textarea
          ref={textRef}
          rows={1}
          value={line.text}
          aria-label={`${speaker.name}’s line`}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              onDone()
            }
          }}
          className="text-ink caret-green w-full resize-none overflow-hidden bg-transparent text-[16px] leading-[23px] font-medium outline-none"
        />
      ) : (
        <button
          type="button"
          onClick={onEdit}
          className="text-ink w-full cursor-text text-left text-[16px] leading-[23px] font-medium"
        >
          {line.text || <span className="text-muted">Write this line</span>}
        </button>
      )}

      {editing ? (
        <div className="flex items-center gap-[10px] text-[13px]">
          <button
            type="button"
            onClick={onDone}
            className="bg-green text-page hover:bg-green-2 rounded-full px-[14px] py-[6px] font-semibold transition-colors"
          >
            Done
          </button>
          <span className="text-muted whitespace-nowrap">{editHint}</span>
        </div>
      ) : (
        <p className={cn('text-[13px] whitespace-nowrap', state === 'playing' ? 'text-green' : 'text-muted')}>
          {loading ? 'Getting the voice…' : state === 'playing' ? `Playing, ${clock(line.seconds)}` : clock(line.seconds)}
        </p>
      )}
    </article>
  )
}
