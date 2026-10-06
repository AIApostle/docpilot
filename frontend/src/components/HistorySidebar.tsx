import type { ChatSummary } from '../api'
import { Brand } from './Brand'
import { Icon } from './Icon'

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
}: HistorySidebarProps) {
  return (
    <>
      {isOpen && (
        <button
          aria-label="Close conversation history"
          className="mobile-scrim"
          onClick={onClose}
          type="button"
        />
      )}
      <aside className={`history-sidebar${isOpen ? ' history-sidebar-open' : ''}`}>
        <div className="sidebar-top">
          <Brand />
          <button
            aria-label="Close history"
            className="icon-button sidebar-close"
            onClick={onClose}
            type="button"
          >
            <Icon name="close" />
          </button>
        </div>

        <button className="new-conversation-button" disabled={previewMode} onClick={onNew} type="button">
          <Icon name="plus" size={17} />
          <span>New conversation</span>
        </button>

        <div className="history-heading">
          <h2>History</h2>
          {!previewMode && (
            <button
              aria-label="Refresh conversation history"
              className={`icon-button history-refresh${isRefreshing ? ' is-spinning' : ''}`}
              disabled={isRefreshing}
              onClick={onRefresh}
              type="button"
            >
              <Icon name="refresh" size={16} />
            </button>
          )}
        </div>

        <nav aria-label="Conversation history" className="history-list">
          {chats.length === 0 ? (
            <p className="history-empty">
              Conversations you start will be indexed here.
            </p>
          ) : (
            chats.map((chat) => (
              <button
                aria-current={chat.id === activeId ? 'page' : undefined}
                className={`history-item${chat.id === activeId ? ' history-item-active' : ''}`}
                key={chat.id}
                onClick={() => onSelect(chat.id)}
                type="button"
              >
                <span className="history-item-title">{chat.title || 'Untitled conversation'}</span>
                <span className="history-item-date">{formatDate(chat.updatedAt)}</span>
              </button>
            ))
          )}
        </nav>

        <div className="sidebar-bottom">
          <p className="sidebar-note">
            {previewMode ? 'Synthetic development preview · no conversation data is saved.' : 'A private index of your conversations.'}
          </p>
          {!previewMode && (
            <button className="signout-button" onClick={onLogout} type="button">
              <Icon name="logout" size={16} />
              Sign out
            </button>
          )}
        </div>
      </aside>
    </>
  )
}
