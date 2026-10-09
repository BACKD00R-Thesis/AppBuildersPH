import { cn } from '../lib/cn'

interface Props<T extends string | number> {
  label: string
  options: { value: T; label: string }[]
  value: T
  onChange: (value: T) => void
  /** Laptop segments are 36px tall, mobile 38px. */
  density: 'desktop' | 'mobile'
}

/** Figma: Segmented. One selected pill inside a mint track. */
export function Segmented<T extends string | number>({ label, options, value, onChange, density }: Props<T>) {
  return (
    <div role="radiogroup" aria-label={label} className="flex w-full gap-1 rounded-full bg-mint p-1">
      {options.map((option) => {
        const selected = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(option.value)}
            className={cn(
              'min-w-0 flex-1 rounded-full text-[14px] font-semibold whitespace-nowrap transition-colors',
              density === 'desktop' ? 'py-[9px]' : 'py-[10px]',
              selected ? 'bg-green text-page' : 'text-muted hover:text-ink',
            )}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
