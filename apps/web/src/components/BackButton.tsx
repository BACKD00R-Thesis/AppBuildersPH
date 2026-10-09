import { Link } from 'react-router-dom'
import { Icon } from './Icon'

/** Figma: IconButton/back. Lives on green headers. */
export function BackButton({ to, label = 'Back' }: { to: string; label?: string }) {
  return (
    <Link
      to={to}
      aria-label={label}
      className="bg-green-2 flex size-10 shrink-0 items-center justify-center rounded-full"
    >
      <Icon name="back20" />
    </Link>
  )
}
