import { Link } from 'react-router-dom'
import { Icon } from '../components/Icon'

/**
 * Figma: Tab bar (Home screen only). Only the Home tab has an active state in the design,
 * and the Library and Engine tabs have no screens yet, so those two are not links.
 */
export function TabBar() {
  return (
    <nav
      aria-label="Main"
      className="border-mint-line bg-card flex w-full shrink-0 items-center justify-between border-t px-[22px] pt-[10px] pb-[max(env(safe-area-inset-bottom),28px)]"
    >
      <Link
        to="/"
        aria-current="page"
        className="bg-green text-page flex items-center gap-2 rounded-full px-4 py-[10px] text-[14px] font-semibold whitespace-nowrap"
      >
        <Icon name="homeLight18" />
        Home
      </Link>
      <span className="flex size-11 items-center justify-center" aria-label="Library" aria-disabled>
        <Icon name="gridMuted22" />
      </span>
      <Link to="/new" aria-label="New video" className="flex size-11 items-center justify-center">
        <Icon name="plusMuted22" />
      </Link>
      <span className="flex size-11 items-center justify-center" aria-label="Engine" aria-disabled>
        <Icon name="chipMuted22" />
      </span>
    </nav>
  )
}
