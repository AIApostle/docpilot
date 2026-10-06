import type { ChatMessage } from '../api'
import type { Route } from '../routes'
import type { RefObject } from 'react'
import { Icon } from './Icon'

interface ConversationPanelProps {
  route: Route
  messages: ChatMessage[]
  conversationLoaded: boolean
  threadLoading: boolean
  sending: boolean
  messagesEndRef: RefObject<HTMLDivElement | null>
  onDraftChange: (value: string) => void
  onRetryConversation: () => void
}

export function ConversationPanel({
  route,
  messages,
  conversationLoaded,
  threadLoading,
  sending,
  messagesEndRef,
  onDraftChange,
  onRetryConversation,
}: ConversationPanelProps) {
  const selectedId = route.kind === 'chat' ? route.id : undefined
  const isNew = route.kind === 'new'

  if (threadLoading) {
    return (
      <section aria-label="Conversation" className="conversation-panel">
        <div className="thread-loading" role="status">
          <span className="loading-rule" />
          <p>Opening conversation…</p>
        </div>
      </section>
    )
  }

  if (selectedId && !conversationLoaded) {
    return (
      <section aria-label="Conversation" className="conversation-panel">
        <div className="thread-loading thread-open-error">
          <p>We couldn’t open this conversation.</p>
          <button className="text-button" onClick={onRetryConversation} type="button">
            Try again
          </button>
        </div>
      </section>
    )
  }

  if (selectedId && messages.length === 0) {
    return (
      <section aria-label="Conversation" className="conversation-panel">
        <div className="thread-loading">
          <p>This conversation has no messages yet.</p>
        </div>
      </section>
    )
  }

  if (messages.length === 0 && isNew) {
    return (
      <section aria-label="Conversation" className="conversation-panel">
        <div className="empty-page">
          <span className="empty-page-mark" aria-hidden="true">
            <Icon name="book" size={30} />
          </span>
          <h2>What would you like to remember?</h2>
          <p className="empty-page-copy">
            Ask about documented patient history or add a note from a visit.
          </p>
          <div className="prompt-lines" aria-label="Example prompts">
            <button onClick={() => onDraftChange('What information is documented about a patient?')} type="button">
              <span>Ask</span>
              <span>What information is documented about a patient?</span>
              <Icon name="chevron" size={16} />
            </button>
            <button onClick={() => onDraftChange('Add a note from a recent visit.')} type="button">
              <span>Record</span>
              <span>Add a note from a recent visit.</span>
              <Icon name="chevron" size={16} />
            </button>
            <button onClick={() => onDraftChange('Is an allergy documented for this patient?')} type="button">
              <span>Check</span>
              <span>Is an allergy documented for this patient?</span>
              <Icon name="chevron" size={16} />
            </button>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section aria-label="Conversation" className="conversation-panel">
      <div className="message-list">
        {messages.map((message, index) => (
          <article
            className={`message-row message-${message.role}`}
            key={message.id || `${message.role}-${index}`}
          >
            <div className="message-author">
              {message.role === 'assistant'
                ? <span className="assistant-mark"><Icon name="book" size={16} /></span>
                : <span className="user-mark" aria-hidden="true">You</span>}
              <span>{message.role === 'assistant' ? 'DocPilot' : 'You'}</span>
            </div>
            <p className="message-content">{message.content}</p>
          </article>
        ))}
        {sending && (
          <div className="assistant-thinking" role="status">
            <span className="thinking-dot" />
            <span>Checking documented memories…</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </section>
  )
}
