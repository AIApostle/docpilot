import { useEffect, useRef } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { Icon } from './Icon'

interface MessageComposerProps {
  value: string
  busy: boolean
  previewMode: boolean
  onChange: (value: string) => void
  onSend: (message: string) => Promise<void>
}

export function MessageComposer({ value, busy, previewMode, onChange, onSend }: MessageComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const message = value.trim()
    if (message && !busy && !previewMode) void onSend(message)
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !previewMode) {
      event.preventDefault()
      const message = value.trim()
      if (message && !busy) void onSend(message)
    }
  }

  useEffect(() => {
    const field = textareaRef.current
    if (!field) return
    field.style.height = 'auto'
    field.style.height = `${Math.min(field.scrollHeight, 168)}px`
  }, [value])

  return (
    <div className="composer-wrap">
      <form className="message-composer" onSubmit={handleSubmit}>
        <label className="visually-hidden" htmlFor="message-input">Message DocPilot</label>
        <textarea
          disabled={previewMode}
          id="message-input"
          maxLength={6000}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={previewMode ? 'Read-only preview — sign in to send messages.' : 'Ask about documented history or add a visit update…'}
          ref={textareaRef}
          rows={1}
          value={value}
        />
        <div className="composer-actions">
          <span>{previewMode ? 'Development preview · messages are not sent' : 'Enter to send · Shift + Enter for a new line'}</span>
          <button
            aria-label={busy ? 'Sending message' : 'Send message'}
            className="send-button"
            disabled={previewMode || busy || !value.trim()}
            type="submit"
          >
            {busy ? <span className="send-spinner" /> : <Icon name="send" size={18} />}
          </button>
        </div>
      </form>
      <p className="composer-disclaimer">
        DocPilot recalls what’s documented. It does not diagnose or recommend treatment.
      </p>
    </div>
  )
}
