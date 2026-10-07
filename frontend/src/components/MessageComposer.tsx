import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent, FormEvent, KeyboardEvent } from 'react'
import type { ChatAttachment } from '../api'
import { Icon } from './Icon'
import { ui } from '../ui'

interface MessageComposerProps {
  value: string
  busy: boolean
  previewMode: boolean
  onChange: (value: string) => void
  onSend: (message: string, attachments: ChatAttachment[]) => Promise<boolean>
}

export function MessageComposer({ value, busy, previewMode, onChange, onSend }: MessageComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<File[]>([])
  const [fileError, setFileError] = useState('')
  const [preparing, setPreparing] = useState(false)

  async function encodeFile(file: File): Promise<ChatAttachment> {
    const bytes = new Uint8Array(await file.arrayBuffer())
    let binary = ''
    for (let offset = 0; offset < bytes.length; offset += 0x8000) {
      binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000))
    }
    return {
      filename: file.name,
      file_type: file.type || 'application/octet-stream',
      content_base64: window.btoa(binary),
    }
  }

  function handleFileSelection(event: ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(event.currentTarget.files ?? [])
    event.currentTarget.value = ''
    setFileError('')
    if (selected.length + files.length > 5) {
      setFileError('Attach up to 5 files per message.')
      return
    }
    if (selected.some((file) => file.size > 10 * 1024 * 1024)) {
      setFileError('Each file must be 10 MB or smaller.')
      return
    }
    const totalSize = [...files, ...selected].reduce((total, file) => total + file.size, 0)
    if (totalSize > 20 * 1024 * 1024) {
      setFileError('Combined attachments must be 20 MB or smaller.')
      return
    }
    setFiles((current) => [...current, ...selected])
  }

  async function submitMessage() {
    const message = value.trim()
    if ((!message && files.length === 0) || busy || preparing || previewMode) return
    setPreparing(true)
    setFileError('')
    try {
      const attachments = await Promise.all(files.map(encodeFile))
      if (await onSend(message, attachments)) setFiles([])
    } catch {
      setFileError('The selected files could not be prepared. Please try again.')
    } finally {
      setPreparing(false)
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void submitMessage()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !previewMode) {
      event.preventDefault()
      void submitMessage()
    }
  }

  useEffect(() => {
    const field = textareaRef.current
    if (!field) return
    field.style.height = 'auto'
    field.style.height = `${Math.min(field.scrollHeight, 168)}px`
  }, [value])

  return (
    <div className={ui.composerWrap}>
      <form className={ui.composer} onSubmit={handleSubmit}>
        <label className="visually-hidden" htmlFor="message-input">Message DocPilot</label>
        <textarea
          className={ui.composerTextarea}
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
        {files.length > 0 && (
          <div aria-label="Attached files" className={ui.fileList}>
            {files.map((file, index) => (
              <span className={ui.fileChip} key={`${file.name}-${file.lastModified}-${index}`}>
                <Icon name="paperclip" size={14} />
                <span>{file.name}</span>
                <button
                  aria-label={`Remove ${file.name}`}
                  onClick={() => setFiles((current) => current.filter((_, fileIndex) => fileIndex !== index))}
                  type="button"
                >
                  <Icon name="close" size={13} />
                </button>
              </span>
            ))}
          </div>
        )}
        <div className={ui.composerActions}>
          <div className={ui.composerTools}>
            <input
              accept=".pdf,.txt,.csv,image/*,audio/*"
              className="visually-hidden"
              disabled={previewMode || busy || preparing || files.length >= 5}
              multiple
              onChange={handleFileSelection}
              ref={fileInputRef}
              type="file"
            />
            <button
              aria-label="Attach files"
              className={ui.attachButton}
              disabled={previewMode || busy || preparing || files.length >= 5}
              onClick={() => fileInputRef.current?.click()}
              title="Attach files (up to 5 files, 10 MB each)"
              type="button"
            >
              <Icon name="paperclip" size={18} />
            </button>
            <span>{previewMode ? 'Development preview · messages are not sent' : 'Enter to send · Shift + Enter for a new line'}</span>
          </div>
          <button
            aria-label={busy || preparing ? 'Preparing message' : 'Send message'}
            className={ui.sendButton}
            disabled={previewMode || busy || preparing || (!value.trim() && files.length === 0)}
            type="submit"
          >
            {busy || preparing ? <span className="size-5 animate-spin rounded-full border-2 border-white/40 border-t-white" /> : <Icon name="send" size={18} />}
          </button>
        </div>
      </form>
      {fileError && <p className="mt-2 text-sm text-danger" role="alert">{fileError}</p>}
      <p className={ui.composerDisclaimer}>
        DocPilot recalls what’s documented. It does not diagnose or recommend treatment.
      </p>
    </div>
  )
}
