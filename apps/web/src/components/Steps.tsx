import { cn } from '../lib/cn'
import type { StepStatus } from '../lib/types'
import { Icon } from './Icon'

interface Props {
  items: { id: string; label: string; status: StepStatus }[]
  density: 'desktop' | 'mobile'
}

/** Figma: Steps. Done = green check, current = ring with dot and bolder label, pending = empty ring. */
export function Steps({ items, density }: Props) {
  return (
    <ul
      className={cn(
        'bg-card rounded-card flex w-full flex-col gap-4',
        density === 'desktop' ? 'shadow-card p-[22px] text-[16px]' : 'shadow-card-sm p-5 text-[15px]',
      )}
    >
      {items.map((item) => (
        <li key={item.id} className="flex items-center gap-3" aria-current={item.status === 'current' ? 'step' : undefined}>
          {item.status === 'done' && (
            <span className="bg-green flex size-7 shrink-0 items-center justify-center rounded-full">
              <Icon name="checkLight16" />
            </span>
          )}
          {item.status === 'current' && <Icon name="stepCurrent28" />}
          {item.status === 'pending' && <span className="border-mint-line bg-card size-7 shrink-0 rounded-full border-2" />}
          <span
            className={cn(
              'whitespace-nowrap',
              item.status === 'current' && 'text-ink font-semibold',
              item.status === 'done' && 'text-ink',
              item.status === 'pending' && 'text-muted',
            )}
          >
            {item.label}
          </span>
        </li>
      ))}
    </ul>
  )
}
