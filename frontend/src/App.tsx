import { useCallback, useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import {
  ApiError,
  connectTelegram,
  disconnectTelegram,
  getChat,
  getChats,
  login,
  logout,
  register,
  sendChatMessage,
} from './api'
import type { ChatAttachment, ChatDetail, ChatMessage, ChatSummary, TelegramConnectPayload } from './api'
import { AuthScreen } from './components/AuthScreen'
import { Brand } from './components/Brand'
import { ChatWorkspace } from './components/ChatWorkspace'
import { Icon } from './components/Icon'
import { TelegramSetupPage } from './components/TelegramSetupPage'
import { demoConversation, demoHistory } from './data/demoConversation'
import { isDemoRoute, resolveRoute } from './routes'
import './App.css'

function errorText(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'DocPilot could not reach the server. Check your connection and try again.'
}

function initialSessionState(): 'checking' | 'authenticated' | 'guest' {
  const route = resolveRoute(window.location.pathname)
  if (isDemoRoute(route)) return 'authenticated'
  if (route.kind === 'login' || route.kind === 'register') return 'guest'
  return 'checking'
}

function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname)
  const [sessionState, setSessionState] = useState<'checking' | 'authenticated' | 'guest' | 'error'>(initialSessionState)
  const [sessionError, setSessionError] = useState('')
  const [authError, setAuthError] = useState('')
  const [authBusy, setAuthBusy] = useState(false)
  const [history, setHistory] = useState<ChatSummary[]>(() => (
    isDemoRoute(resolveRoute(window.location.pathname)) ? demoHistory : []
  ))
  const [activeConversation, setActiveConversation] = useState<ChatDetail | null>(() => (
    isDemoRoute(resolveRoute(window.location.pathname)) ? demoConversation : null
  ))
  const [conversationLoading, setConversationLoading] = useState(() => {
    const route = resolveRoute(window.location.pathname)
    return route.kind === 'chat' && !isDemoRoute(route)
  })
  const [conversationReload, setConversationReload] = useState(0)
  const [threadError, setThreadError] = useState('')
  const [historyError, setHistoryError] = useState('')
  const [historyBusy, setHistoryBusy] = useState(false)
  const [sending, setSending] = useState(false)
  const [draft, setDraft] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const [logoutError, setLogoutError] = useState('')
  const [telegramState, setTelegramState] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [telegramBusy, setTelegramBusy] = useState(false)
  const route = useMemo(() => resolveRoute(currentPath), [currentPath])
  const previewMode = isDemoRoute(route)

  const navigate = useCallback((path: string, replace = false, force = false) => {
    let nextPath = path
    const requestedRoute = resolveRoute(path)
    const requestedAuthRoute = requestedRoute.kind === 'login' || requestedRoute.kind === 'register'
    if (!force && sessionState === 'authenticated' && requestedAuthRoute) nextPath = '/new'
    if (!force && sessionState === 'guest' && !requestedAuthRoute) nextPath = '/login'
    if (window.location.pathname !== nextPath) {
      if (replace) window.history.replaceState({}, '', nextPath)
      else window.history.pushState({}, '', nextPath)
    }
    setCurrentPath(nextPath)
    setMenuOpen(false)
    setThreadError('')
    const nextRoute = resolveRoute(nextPath)
    setConversationLoading(
      nextRoute.kind === 'chat'
      && !isDemoRoute(nextRoute)
      && activeConversation?.id !== nextRoute.id,
    )
  }, [activeConversation?.id, sessionState])

  useEffect(() => {
    const handlePopState = () => navigate(window.location.pathname, true)
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [navigate])

  async function loadSession() {
    try {
      const chats = await getChats()
      setHistory(chats)
      setSessionState('authenticated')
      if (resolveRoute(window.location.pathname).kind === 'missing') navigate('/new', true, true)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setSessionState('guest')
        navigate('/login', true, true)
        return
      }
      setSessionError(errorText(error))
      setSessionState('error')
    }
  }

  useEffect(() => {
    const initialRoute = resolveRoute(window.location.pathname)
    if (initialRoute.kind === 'login' || initialRoute.kind === 'register' || isDemoRoute(initialRoute)) return

    let cancelled = false
    void getChats()
      .then((chats) => {
        if (cancelled) return
        setHistory(chats)
        setSessionState('authenticated')
        if (resolveRoute(window.location.pathname).kind === 'missing') navigate('/new', true, true)
      })
      .catch((error: unknown) => {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          setSessionState('guest')
          navigate('/login', true, true)
          return
        }
        setSessionError(errorText(error))
        setSessionState('error')
      })

    return () => {
      cancelled = true
    }
  }, [navigate])

  useEffect(() => {
    if (sessionState !== 'authenticated' || route.kind !== 'chat' || previewMode) return
    if (activeConversation?.id === route.id) return

    let cancelled = false
    void getChat(route.id)
      .then((conversation) => {
        if (!cancelled) {
          setActiveConversation(conversation)
          setConversationLoading(false)
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setThreadError(errorText(error))
          setConversationLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [activeConversation?.id, conversationReload, previewMode, route, sessionState])

  async function handleAuth(credentials: { name?: string; email: string; password: string }) {
    setAuthBusy(true)
    setAuthError('')
    try {
      const isRegister = route.kind === 'register'
      if (isRegister) {
        await register(credentials)
        toast.success('Your DocPilot account is ready.')
      } else {
        await login(credentials)
        toast.success('Welcome back.')
      }
      const chats = await getChats()
      setHistory(chats)
      setSessionState('authenticated')
      setDraft('')
      navigate('/new', false, true)
    } catch (error) {
      setAuthError(errorText(error))
    } finally {
      setAuthBusy(false)
    }
  }

  async function refreshHistory() {
    if (previewMode) return
    setHistoryBusy(true)
    setHistoryError('')
    try {
      setHistory(await getChats())
    } catch (error) {
      setHistoryError(errorText(error))
    } finally {
      setHistoryBusy(false)
    }
  }

  async function sendMessage(message: string, attachments: ChatAttachment[] = []): Promise<boolean> {
    if (previewMode || sending || (!message.trim() && attachments.length === 0)) return false
    const previousConversation = route.kind === 'chat' && activeConversation?.id === route.id
      ? activeConversation
      : null
    if (route.kind === 'chat' && !previousConversation) return false
    const existingId = previousConversation?.id
    const draftAtSend = draft
    const now = new Date().toISOString()
    const messageText = message.trim() || 'Attached files'
    const userMessage: ChatMessage = {
      id: `local-user-${Date.now()}`,
      role: 'user',
      content: messageText,
      createdAt: now,
      attachments: attachments.map(({ filename, file_type }) => ({ filename, file_type })),
    }

    setSending(true)
    setThreadError('')
    setActiveConversation((current) => ({
      id: current?.id ?? '',
      title: current?.title ?? 'New conversation',
      updatedAt: now,
      messages: [
        ...(route.kind === 'chat' && current?.id === route.id ? current.messages : []),
        userMessage,
      ],
    }))

    try {
      const result = await sendChatMessage(messageText, existingId, attachments)
      const assistantMessage: ChatMessage = {
        id: `local-assistant-${Date.now()}`,
        role: 'assistant',
        content: result.reply,
        createdAt: result.updatedAt ?? new Date().toISOString(),
      }
      const title = previousConversation?.title || result.title || messageText.replace(/\s+/g, ' ').slice(0, 72)
      const conversation: ChatDetail = {
        id: result.id,
        title,
        updatedAt: result.updatedAt ?? new Date().toISOString(),
        messages: [...(previousConversation?.messages ?? []), userMessage, assistantMessage],
      }
      setActiveConversation(conversation)
      setDraft((currentDraft) => currentDraft === draftAtSend ? '' : currentDraft)
      setHistory((current) => [
        { id: conversation.id, title: conversation.title, updatedAt: conversation.updatedAt },
        ...current.filter((chat) => chat.id !== conversation.id),
      ])
      if (!existingId) {
        navigate(`/chat/${encodeURIComponent(result.id)}`, false, true)
        setConversationLoading(false)
      }
      return true
    } catch (error) {
      setActiveConversation(previousConversation)
      setThreadError(errorText(error))
      return false
    } finally {
      setSending(false)
    }
  }

  async function handleLogout() {
    setLogoutError('')
    try {
      await logout()
      setSessionState('guest')
      setHistory([])
      setActiveConversation(null)
      setDraft('')
      navigate('/login', false, true)
    } catch (error) {
      setLogoutError(errorText(error))
    }
  }

  async function handleTelegramConnect(payload: TelegramConnectPayload) {
    setTelegramBusy(true)
    setTelegramState(null)
    try {
      await connectTelegram(payload)
      setTelegramState({ type: 'success', message: 'Telegram linked successfully. Your bot should be ready for bedside notes.' })
    } catch (error) {
      setTelegramState({ type: 'error', message: errorText(error) })
    } finally {
      setTelegramBusy(false)
    }
  }

  async function handleTelegramDisconnect() {
    setTelegramBusy(true)
    setTelegramState(null)
    try {
      await disconnectTelegram()
      setTelegramState({ type: 'success', message: 'Telegram disconnected from your doctor account.' })
    } catch (error) {
      setTelegramState({ type: 'error', message: errorText(error) })
    } finally {
      setTelegramBusy(false)
    }
  }

  if (route.kind === 'login' || route.kind === 'register') {
    return (
      <AuthScreen
        busy={authBusy}
        error={authError}
        mode={route.kind}
        onNavigate={navigate}
        onSubmit={handleAuth}
      />
    )
  }

  if (sessionState === 'checking') {
    return (
      <main className="session-screen" role="status">
        <span className="loading-rule" />
        <p>Opening your conversation index…</p>
      </main>
    )
  }

  if (sessionState === 'error') {
    return (
      <main className="session-screen session-error">
        <Brand />
        <h1>We couldn’t open your memory.</h1>
        <p role="alert">{sessionError}</p>
        <button
          className="button-primary"
          onClick={() => {
            setSessionState('checking')
            setSessionError('')
            void loadSession()
          }}
          type="button"
        >
          Try again
        </button>
        <button className="text-button" onClick={() => navigate('/login')} type="button">
          Go to sign in
        </button>
      </main>
    )
  }

  if (route.kind === 'telegram' && sessionState === 'authenticated') {
    return (
      <TelegramSetupPage
        busy={telegramBusy}
        error={telegramState?.type === 'error' ? telegramState.message : undefined}
        onBack={() => navigate('/new', false, true)}
        onConnect={handleTelegramConnect}
        onDisconnect={handleTelegramDisconnect}
        success={telegramState?.type === 'success' ? telegramState.message : undefined}
      />
    )
  }

  if (sessionState !== 'authenticated') return null

  return (
    <>
      {logoutError && (
        <div className="global-alert" role="alert">
          <span>{logoutError}</span>
          <button aria-label="Dismiss sign-out error" onClick={() => setLogoutError('')} type="button">
            <Icon name="close" size={16} />
          </button>
        </div>
      )}
      <ChatWorkspace
        activeConversation={
          route.kind === 'chat' && activeConversation?.id === route.id && !conversationLoading
            ? activeConversation
            : null
        }
        chats={history}
        draft={draft}
        historyError={historyError}
        menuOpen={menuOpen}
        onCloseMenu={() => setMenuOpen(false)}
        onDismissThreadError={() => setThreadError('')}
        onDraftChange={setDraft}
        onLogout={() => void handleLogout()}
        onMenu={() => setMenuOpen(true)}
        onNew={() => {
          setThreadError('')
          setDraft('')
          navigate('/new')
        }}
        onRefresh={() => void refreshHistory()}
        onTelegram={() => navigate('/telegram')}
        onRetryConversation={() => {
          setThreadError('')
          setConversationLoading(true)
          setConversationReload((current) => current + 1)
        }}
        onSelectChat={(id) => navigate(`/chat/${encodeURIComponent(id)}`)}
        onSend={sendMessage}
        previewMode={previewMode}
        refreshing={historyBusy}
        route={route}
        sending={sending}
        threadError={threadError}
      />
    </>
  )
}

export default App
