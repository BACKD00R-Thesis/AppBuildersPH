import { cn } from '../lib/cn'
import { icons, type IconName } from './icons'

/** Decorative icon. Size comes from the SVG file itself, so don't set width/height. */
export function Icon({ name, className }: { name: IconName; className?: string }) {
  return <img src={icons[name]} alt="" draggable={false} className={cn('block shrink-0', className)} />
}
