import type { ReactNode } from 'react'
import { BackButton } from '../components/BackButton'
import { cn } from '../lib/cn'

interface Props {
  /** Content of the green header, below the top safe area. */
  header: ReactNode
  /** Extra classes for the header (gap and bottom padding differ per screen). */
  headerClassName?: string
  /** Gap between body children differs per screen. */
  bodyClassName?: string
  /** Pinned under the body: action buttons or the tab bar. */
  footer?: ReactNode
  children: ReactNode
}

/**
 * Figma: every Mobile v2 screen is a green header, a page-colored sheet with 28px top corners,
 * and a pinned bottom bar. The phone bezel and the "9:41 / 5G 83%" status bar in the mockup are
 * device chrome, so they are not rendered; the top safe area takes their place.
 */
export function MobileShell({ header, headerClassName, bodyClassName, footer, children }: Props) {
  return (
    <div className="bg-green mx-auto flex h-full w-full max-w-[480px] flex-col">
      <header
        className={cn(
          'relative flex w-full shrink-0 flex-col overflow-clip px-5 pt-[max(env(safe-area-inset-top),18px)]',
          headerClassName,
        )}
      >
        {header}
      </header>
      <main
        className={cn(
          'bg-page flex min-h-0 w-full flex-1 flex-col overflow-y-auto rounded-t-[28px] px-5 pt-[22px] pb-[14px]',
          bodyClassName,
        )}
      >
        {children}
      </main>
      {footer}
    </div>
  )
}

/** Back button plus screen name, used on every mobile screen except Home and Player. */
export function MobileTitleRow({ backTo, title }: { backTo: string; title: string }) {
  return (
    <div className="flex w-full items-center gap-3">
      <BackButton to={backTo} />
      <h1 className="text-page text-[17px] font-semibold whitespace-nowrap">{title}</h1>
    </div>
  )
}

/** Figma: Bottom bar. */
export function MobileBottomBar({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <footer
      className={cn(
        'bg-page flex w-full shrink-0 flex-col items-center px-5 pt-[10px] pb-[max(env(safe-area-inset-bottom),30px)]',
        className,
      )}
    >
      {children}
    </footer>
  )
}
