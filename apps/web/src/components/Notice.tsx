import type { ReactNode } from 'react'
import { cn } from '../lib/cn'

/**
 * Inline message for errors and empty states. Not in the Figma file, so it stays quiet:
 * a mint card with clay text for problems, muted text otherwise.
 */
export function Notice({
  children,
  tone = 'error',
  action,
  className,
}: {
  children: ReactNode
  tone?: 'error' | 'info'
  action?: ReactNode
  className?: string
}) {
  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={cn(
        'bg-mint rounded-card flex w-full shrink-0 items-center gap-3 px-4 py-3 text-[14px] leading-[20px]',
        tone === 'error' ? 'text-clay-deep' : 'text-muted',
        className,
      )}
    >
      <p className="min-w-0 flex-1">{children}</p>
      {action}
    </div>
  )
}

/** Small text button for use inside a Notice. */
export function NoticeAction({ onClick, children }: { onClick: () => void; children: ReactNode }) {
  return (
    <button type="button" onClick={onClick} className="text-green shrink-0 text-[14px] font-semibold whitespace-nowrap">
      {children}
    </button>
  )
}
