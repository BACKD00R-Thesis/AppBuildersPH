import { cn } from '../lib/cn'
import { Icon } from './Icon'

/** Figma: Key ideas ("What this video covers"). */
export function KeyIdeas({ ideas, density }: { ideas: string[]; density: 'desktop' | 'mobile' }) {
  const desktop = density === 'desktop'
  return (
    <section
      className={cn(
        'bg-card rounded-card flex w-full flex-col',
        desktop ? 'shadow-card gap-[14px] p-[22px]' : 'shadow-card-sm gap-[10px] p-4',
      )}
    >
      <h2 className={cn('text-ink font-serif font-semibold', desktop ? 'text-[20px]' : 'text-[17px]')}>
        What this video covers
      </h2>
      <ul className={cn('flex flex-col', desktop ? 'gap-[14px]' : 'gap-[10px]')}>
        {ideas.map((idea) => (
          <li key={idea} className={cn('flex items-center', desktop ? 'gap-3 text-[15px]' : 'gap-[10px] text-[14px]')}>
            <span
              className={cn(
                'bg-mint flex shrink-0 items-center justify-center rounded-full',
                desktop ? 'size-6' : 'size-[22px]',
              )}
            >
              <Icon name={desktop ? 'checkGreen14' : 'checkGreen13'} />
            </span>
            <span className="text-ink">{idea}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
