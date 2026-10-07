import type { ChatSummary } from '../api'
import { Brand } from './Brand'
import { Icon } from './Icon'
import { ui } from '../ui'

interface HistorySidebarProps {
  chats: ChatSummary[]
  activeId?: string
  isOpen: boolean
  isRefreshing: boolean
  previewMode: boolean
  onClose: () => void
  onLogout: () => void
  onNew: () => void
  onRefresh: () => void
  onSelect: (id: string) => void
  onTelegram: () => void
}

function formatDate(value?: string): string {
  if (!value) return 'Saved'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Saved'

  const today = new Date()
  const isToday = date.toDateString() === today.toDateString()
  if (isToday) {
    return new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(date)
  }
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(date)
}

export function HistorySidebar({
  chats,
  activeId,
  isOpen,
  isRefreshing,
  previewMode,
  onClose,
  onLogout,
  onNew,
  onRefresh,
  onSelect,
  onTelegram,
}: HistorySidebarProps) {
  return (
    <>
      {isOpen && (
        <button
          aria-label="Close conversation history"
          className="fixed inset-0 z-30 h-full w-full bg-ink/35 min-[701px]:hidden"
          onClick={onClose}
          type="button"
        />
      )}
      <aside className={`${ui.sidebar} ${isOpen ? ui.sidebarOpen : ''}`}>
        <div className={ui.sidebarTop}>
          <Brand />
          <button
            aria-label="Close history"
            className={`${ui.iconButton} ${ui.sidebarClose}`}
            onClick={onClose}
            type="button"
          >
            <Icon name="close" />
          </button>
        </div>

        <button className={ui.newConversation} disabled={previewMode} onClick={onNew} type="button">
          <Icon name="plus" size={17} />
          <span>New conversation</span>
        </button>

        <div className={ui.historyHeading}>
          <h2 className={ui.historyHeadingText}>History</h2>
          {!previewMode && (
            <button
              aria-label="Refresh conversation history"
              className={`${ui.iconButton} ${isRefreshing ? 'animate-spin' : ''}`}
              disabled={isRefreshing}
              onClick={onRefresh}
              type="button"
            >
              <Icon name="refresh" size={16} />
            </button>
          )}
        </div>

        <nav aria-label="Conversation history" className={ui.historyList}>
          {chats.length === 0 ? (
            <p className={ui.historyEmpty}>
              Conversations you start will be indexed here.
            </p>
          ) : (
            chats.map((chat) => (
              <button
                aria-current={chat.id === activeId ? 'page' : undefined}
                className={`${ui.historyItem} ${chat.id === activeId ? ui.historyItemActive : ''}`}
                key={chat.id}
                onClick={() => onSelect(chat.id)}
                type="button"
              >
                <span className={ui.historyItemTitle}>{chat.title || 'Untitled conversation'}</span>
                <span className={ui.historyItemDate}>{formatDate(chat.updatedAt)}</span>
              </button>
            ))
          )}
        </nav>

        <div className={ui.sidebarBottom}>
          <p className={ui.sidebarNote}>
            {previewMode ? 'Synthetic development preview · no conversation data is saved.' : 'A private index of your conversations.'}
          </p>
          {!previewMode && (
            <>
              <button className={ui.telegramButton} onClick={onTelegram} type="button">
                <Icon name="book" size={16} />
                Connect Telegram
              </button>
              <button className={ui.signoutButton} onClick={onLogout} type="button">
                <Icon name="logout" size={16} />
                Sign out
              </button>
            </>
          )}
        </div>
      </aside>
    </>
  )
}
