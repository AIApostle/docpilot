import { Icon } from './Icon'

export function Brand({ inverse = false }: { inverse?: boolean }) {
  return (
    <a
      aria-label="DocPilot home"
      className={`brand${inverse ? ' brand-inverse' : ''}`}
      href="/new"
    >
      <span className="brand-mark">
        <Icon name="book" size={23} />
      </span>
      <span>DocPilot</span>
    </a>
  )
}
