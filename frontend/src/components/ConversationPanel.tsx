import type { ChatMessage } from '../api'
import type { Route } from '../routes'
import type { RefObject } from 'react'
import { Icon } from './Icon'
import { ui } from '../ui'

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
      <section aria-label="Conversation" className={ui.conversationPanel}>
        <div className="mx-auto grid h-full min-h-40 place-content-center justify-items-center gap-4 text-ink-soft" role="status">
          <span className="h-1 w-24 animate-pulse rounded bg-green" />
          <p>Opening conversation…</p>
        </div>
      </section>
    )
  }

  if (selectedId && !conversationLoaded) {
    return (
      <section aria-label="Conversation" className={ui.conversationPanel}>
        <div className="mx-auto grid h-full min-h-40 place-content-center justify-items-center gap-4 text-ink-soft">
          <p>We couldn’t open this conversation.</p>
          <button className={ui.textButton} onClick={onRetryConversation} type="button">
            Try again
          </button>
        </div>
      </section>
    )
  }

  if (selectedId && messages.length === 0) {
    return (
      <section aria-label="Conversation" className={ui.conversationPanel}>
        <div className="mx-auto grid h-full min-h-40 place-content-center text-ink-soft">
          <p>This conversation has no messages yet.</p>
        </div>
      </section>
    )
  }

  if (messages.length === 0 && isNew) {
    return (
      <section aria-label="Conversation" className={ui.conversationPanel}>
        <div className={ui.emptyPage}>
          <span className={ui.emptyMark} aria-hidden="true">
            <Icon name="book" size={30} />
          </span>
          <h2 className={ui.emptyTitle}>What would you like to remember?</h2>
          <p className={ui.emptyCopy}>
            Ask about documented patient history or add a note from a visit.
          </p>
          <div className={ui.promptList} aria-label="Example prompts">
            <button className={ui.promptButton} onClick={() => onDraftChange('What information is documented about a patient?')} type="button">
              <span className={ui.promptLabel}>Ask</span>
              <span>What information is documented about a patient?</span>
              <Icon name="chevron" size={16} />
            </button>
            <button className={ui.promptButton} onClick={() => onDraftChange('Add a note from a recent visit.')} type="button">
              <span className={ui.promptLabel}>Record</span>
              <span>Add a note from a recent visit.</span>
              <Icon name="chevron" size={16} />
            </button>
            <button className={ui.promptButton} onClick={() => onDraftChange('Is an allergy documented for this patient?')} type="button">
              <span className={ui.promptLabel}>Check</span>
              <span>Is an allergy documented for this patient?</span>
              <Icon name="chevron" size={16} />
            </button>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section aria-label="Conversation" className={ui.conversationPanel}>
      <div className={ui.messageList}>
        {messages.map((message, index) => (
          <article
            className={`${ui.messageRow} ${message.role === 'user' ? ui.userMessage : ''}`}
            key={message.id || `${message.role}-${index}`}
          >
            <div className={ui.messageAuthor}>
              {message.role === 'assistant'
                ? <span className={ui.assistantMark}><Icon name="book" size={16} /></span>
                : <span className={ui.userMark} aria-hidden="true">You</span>}
              <span>{message.role === 'assistant' ? 'DocPilot' : 'You'}</span>
            </div>
            <p className={ui.messageContent}>{message.content}</p>
            {message.attachments && message.attachments.length > 0 && (
              <ul aria-label="Message attachments" className="mt-1 flex flex-wrap gap-3 text-xs text-ink-quiet">
                {message.attachments.map((attachment, attachmentIndex) => (
                  <li key={`${attachment.filename}-${attachmentIndex}`}>
                    <Icon name="paperclip" size={14} />
                    <span>{attachment.filename}</span>
                  </li>
                ))}
              </ul>
            )}
          </article>
        ))}
        {sending && (
          <div className="flex items-center gap-2 text-sm text-ink-quiet" role="status">
            <span className="size-2 animate-pulse rounded-full bg-green" />
            <span>Checking documented memories…</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </section>
  )
}
