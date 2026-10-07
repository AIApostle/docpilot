export type Route =
  | { kind: 'login' | 'register' | 'new' | 'missing' | 'telegram' }
  | { kind: 'chat'; id: string }

export const DEMO_CHAT_ID = 'demo'

export function resolveRoute(pathname: string): Route {
  const path = pathname.replace(/\/+$/, '') || '/'

  if (path === '/login' || path === '/') return { kind: 'login' }
  if (path === '/register') return { kind: 'register' }
  if (path === '/new') return { kind: 'new' }
  if (path === '/telegram') return { kind: 'telegram' }

  const chatMatch = path.match(/^\/chat\/([^/]+)$/)
  if (chatMatch) {
    try {
      const id = decodeURIComponent(chatMatch[1])
      if (id) return { kind: 'chat', id }
    } catch {
      return { kind: 'missing' }
    }
  }

  return { kind: 'missing' }
}

export function isDemoRoute(route: Route): boolean {
  return import.meta.env.DEV && route.kind === 'chat' && route.id === DEMO_CHAT_ID
}
