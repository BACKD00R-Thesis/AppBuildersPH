import { cn } from '../lib/cn'

/** Figma: Progress. value is 0 to 1. */
export function ProgressBar({ value, label, className }: { value: number; label: string; className?: string }) {
  const pct = Math.round(Math.min(1, Math.max(0, value)) * 100)
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
      className={cn('bg-mint h-2 overflow-clip rounded-full', className)}
    >
      <div className="bg-green h-2 rounded-full" style={{ width: `${value * 100}%` }} />
    </div>
  )
}
