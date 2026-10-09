import { Icon } from './Icon'

interface Props {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
}

/** Figma: Toggle/on. The off state is not in the design; see assets/icons/toggle-off.svg. */
export function Toggle({ label, checked, onChange }: Props) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className="shrink-0 rounded-full"
    >
      <Icon name={checked ? 'toggleOn' : 'toggleOff'} />
    </button>
  )
}
