import { useEffect, useRef } from 'react'
import type { ChatAttachment, ChatDetail, ChatSummary } from '../api'
import type { Route } from '../routes'
import { ConversationPanel } from './ConversationPanel'
import { HistorySidebar } from './HistorySidebar'
import { Icon } from './Icon'
import { MessageComposer } from './MessageComposer'

interface ChatWorkspaceProps {
  route: Route
  chats: ChatSummary[]
  activeConversation: ChatDetail | null
  threadError: string
  historyError: string
  sending: boolean
  refreshing: boolean
  menuOpen: boolean
  draft: string
  previewMode: boolean
  onDraftChange: (value: string) => void
  onSend: (message: string, attachments: ChatAttachment[]) => Promise<boolean>
  onNew: () => void
  onSelectChat: (id: string) => void
  onRefresh: () => void
  onRetryConversation: () => void
  onLogout: () => void
  onTelegram: () => void
  onMenu: () => void
  onCloseMenu: () => void
  onDismissThreadError: () => void
}

export function ChatWorkspace({
  route,
  chats,
  activeConversation,
  threadError,
  historyError,
  sending,
  refreshing,
  menuOpen,
  draft,
  previewMode,
  onDraftChange,
  onSend,
  onNew,
  onSelectChat,
  onRefresh,
  onRetryConversation,
  onLogout,
  onTelegram,
  onMenu,
  onCloseMenu,
  onDismissThreadError,
}: ChatWorkspaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const selectedId = route.kind === 'chat' ? route.id : undefined
  const isNew = route.kind === 'new'
  const conversationTitle = activeConversation?.title || (
    selectedId ? 'Conversation' : 'New conversation'
  )
  const messages = activeConversation?.messages ?? []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ block: 'end', behavior: 'smooth' })
  }, [activeConversation?.messages.length])

  return (
    <div className="app-shell">
      <HistorySidebar
        activeId={selectedId}
        chats={chats}
        isOpen={menuOpen}
        isRefreshing={refreshing}
        onClose={onCloseMenu}
        onLogout={onLogout}
        onNew={onNew}
        onRefresh={onRefresh}
        onSelect={onSelectChat}
        onTelegram={onTelegram}
        previewMode={previewMode}
      />

      <main className="workspace">
        <header className="workspace-header">
          <button
            aria-label="Open conversation history"
            className="icon-button mobile-menu-button"
            onClick={onMenu}
            type="button"
          >
            <Icon name="menu" size={20} />
          </button>
          <div className="workspace-title-wrap">
            <h1>{conversationTitle}</h1>
            <p>
              {previewMode
                ? 'Development preview · messages are read only.'
                : isNew
                  ? 'A fresh page for what you need to remember.'
                  : 'Your saved conversation'}
            </p>
          </div>
          {!previewMode && (
            <button className="header-new-button" onClick={onNew} type="button">
              <Icon name="plus" size={16} />
              <span>New</span>
            </button>
          )}
        </header>

        {historyError && (
          <div className="inline-alert history-alert" role="alert">
            <span>{historyError}</span>
            <button onClick={onRefresh} type="button">Try again</button>
          </div>
        )}
        {threadError && (
          <div className="inline-alert thread-alert" role="alert">
            <span>{threadError}</span>
            <button aria-label="Dismiss message error" onClick={onDismissThreadError} type="button">
              <Icon name="close" size={16} />
            </button>
          </div>
        )}

        <ConversationPanel
          conversationLoaded={Boolean(activeConversation)}
          messages={messages}
          messagesEndRef={messagesEndRef}
          onDraftChange={onDraftChange}
          onRetryConversation={onRetryConversation}
          route={route}
          sending={sending}
          threadLoading={Boolean(selectedId && !activeConversation)}
        />

        <div className="composer-dock">
          <MessageComposer
            busy={sending}
            onChange={onDraftChange}
            onSend={onSend}
            previewMode={previewMode}
            value={draft}
          />
        </div>
      </main>
    </div>
  )
}
