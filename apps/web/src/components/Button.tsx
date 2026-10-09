import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { cn } from '../lib/cn'

type Variant = 'primary' | 'secondary' | 'ghost'

const base =
  'inline-flex items-center justify-center rounded-full px-6 py-[15px] text-[15px] font-semibold whitespace-nowrap transition-colors'

const variants: Record<Variant, string> = {
  primary: 'bg-green text-page hover:bg-green-2',
  secondary: 'bg-mint text-green hover:bg-mint-line',
  ghost: 'border-[1.5px] border-mint-line text-green hover:bg-mint',
}

interface Props extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  variant?: Variant
  /** Renders a router link instead of a button. */
  to?: string
  children: ReactNode
}

/** Figma: v2/Button/Primary, v2/Button/Secondary, v2/Button/Ghost. Buttons are always pills. */
export function Button({ variant = 'primary', to, className, children, ...rest }: Props) {
  const classes = cn(base, variants[variant], className)
  if (to) {
    return (
      <Link to={to} className={classes}>
        {children}
      </Link>
    )
  }
  return (
    <button type="button" className={classes} {...rest}>
      {children}
    </button>
  )
}
