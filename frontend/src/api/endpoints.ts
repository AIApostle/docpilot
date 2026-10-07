function chatPath(id: string): string {
  return `/chats/${encodeURIComponent(id)}`
}

export const apiEndpoints = {
  auth: {
    login: '/auth/login',
    register: '/auth/register',
    logout: '/auth/logout',
    me: '/auth/me',
  },
  chats: {
    list: '/chats',
    detail: chatPath,
    send: '/chat',
  },
  telegram: {
    widgetConfig: '/telegram/widget-config',
    connect: '/telegram/connect',
    disconnect: '/telegram/disconnect',
  },
} as const
