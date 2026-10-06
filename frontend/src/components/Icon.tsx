import type { ReactNode } from 'react'

export type IconName = 'book' | 'plus' | 'refresh' | 'chevron' | 'send' | 'menu' | 'close' | 'logout' | 'lock' | 'arrow'

const iconPaths: Record<IconName, ReactNode> = {
  book: (
    <>
      <path d="M5 4.75h10.1A2.9 2.9 0 0 1 18 7.65v11.6H7.8A2.8 2.8 0 0 1 5 16.45z" />
      <path d="M5 15.2h10.1a2.9 2.9 0 0 1 2.9 2.9M8.2 8.1h5.6M8.2 11.1h5.6" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  refresh: (
    <>
      <path d="M20 7v5h-5M4.7 16.5A8 8 0 0 0 18.8 18M4 17v-5h5" />
      <path d="M5.2 6A8 8 0 0 1 19.3 6" />
    </>
  ),
  chevron: <path d="m9 18 6-6-6-6" />,
  send: (
    <>
      <path d="m21 3-7.2 18-3.9-7.9L2 9.2 21 3Z" />
      <path d="M10 13 21 3" />
    </>
  ),
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  logout: (
    <>
      <path d="M10 17l5-5-5-5M15 12H3" />
      <path d="M12 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5" />
    </>
  ),
  lock: (
    <>
      <rect x="5" y="10" width="14" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3" />
    </>
  ),
  arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
}

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return (
    <svg
      aria-hidden="true"
      className="icon"
      fill="none"
      height={size}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.7"
      viewBox="0 0 24 24"
      width={size}
    >
      {iconPaths[name]}
    </svg>
  )
}
