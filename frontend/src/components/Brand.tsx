import { Icon } from './Icon'
import { ui } from '../ui'

export function Brand({ inverse = false }: { inverse?: boolean }) {
  return (
    <a
      aria-label="DocPilot home"
      className={`${ui.brand} ${inverse ? ui.brandInverse : ''}`}
      href="/new"
    >
      <span className={ui.brandMark}>
        <Icon name="book" size={23} />
      </span>
      <span>DocPilot</span>
    </a>
  )
}
