import { useEffect, useRef } from 'react'
import type { ChatAttachment, ChatDetail, ChatSummary } from '../api'
import type { Route } from '../routes'
import { ConversationPanel } from './ConversationPanel'
import { HistorySidebar } from './HistorySidebar'
import { Icon } from './Icon'
import { MessageComposer } from './MessageComposer'
import { ui } from '../ui'

interface ChatWorkspaceProps {
  route: Route
  chats: ChatSummary[]
  activeConversation: ChatDetail | null
  threadError: string
  historyError: string
  memoryEnabled: boolean
  memoryBusy: boolean
  memoryError: string
  sending: boolean
  statusMessage?: string
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
  onToggleMemory: () => void
}

export function ChatWorkspace({
  route,
  chats,
  activeConversation,
  threadError,
  historyError,
  memoryEnabled,
  memoryBusy,
  memoryError,
  sending,
  statusMessage,
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
  onToggleMemory,
}: ChatWorkspaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const selectedId = route.kind === 'chat' ? route.id : undefined
  const isNew = route.kind === 'new'
  const conversationTitle = selectedId && activeConversation?.messages.length
    ? activeConversation.title || 'Conversation'
    : undefined
  const messages = activeConversation?.messages ?? []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ block: 'end', behavior: 'smooth' })
  }, [activeConversation?.messages.length])

  return (
    <div className={ui.appShell}>
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

      <main className={ui.workspace}>
        <header className={ui.workspaceHeader}>
          <button
            aria-label="Open conversation history"
            className={`${ui.iconButton} ${ui.mobileMenu}`}
            onClick={onMenu}
            type="button"
          >
            <Icon name="menu" size={20} />
          </button>
          <div className={ui.workspaceTitle}>
            {conversationTitle && <h1 className={ui.workspaceTitleText}>{conversationTitle}</h1>}
            <p className={ui.workspaceSubtitle}>
              {previewMode
                ? 'Development preview · messages are read only.'
                : isNew
                  ? 'A fresh page for what you need to remember.'
                  : 'Your saved conversation'}
            </p>
          </div>
          {!previewMode && (
            <button className={ui.headerNew} onClick={onNew} type="button">
              <Icon name="plus" size={16} />
              <span>New</span>
            </button>
          )}
        </header>

        {historyError && (
          <div className={ui.inlineAlert} role="alert">
            <span>{historyError}</span>
            <button onClick={onRefresh} type="button">Try again</button>
          </div>
        )}
        {threadError && (
          <div className={ui.inlineAlert} role="alert">
            <span>{threadError}</span>
            <button aria-label="Dismiss message error" className={ui.iconButton} onClick={onDismissThreadError} type="button">
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
          statusMessage={statusMessage}
          threadLoading={Boolean(selectedId && !activeConversation)}
        />

        <div className={ui.composerDock}>
          <MessageComposer
            busy={sending}
            memoryBusy={memoryBusy}
            memoryEnabled={memoryEnabled}
            memoryError={memoryError}
            onChange={onDraftChange}
            onSend={onSend}
            onToggleMemory={onToggleMemory}
            previewMode={previewMode}
            value={draft}
          />
        </div>
      </main>
    </div>
  )
}
