import { useEffect, useRef, useState } from 'react'
import { getTelegramWidgetConfig } from '../api'
import type { TelegramConnectPayload } from '../api'
import { Brand } from './Brand'
import { Icon } from './Icon'

declare global {
  interface Window {
    onTelegramAuth?: (user: TelegramConnectPayload) => void
  }
}

interface TelegramSetupPageProps {
  busy: boolean
  error?: string
  success?: string
  onBack: () => void
  onConnect: (payload: TelegramConnectPayload) => Promise<void>
  onDisconnect: () => Promise<void>
}

export function TelegramSetupPage({
  busy,
  error,
  success,
  onBack,
  onConnect,
  onDisconnect,
}: TelegramSetupPageProps) {
  const widgetRef = useRef<HTMLDivElement>(null)
  const onConnectRef = useRef(onConnect)
  const [botUsername, setBotUsername] = useState('')
  const [widgetError, setWidgetError] = useState('')

  useEffect(() => {
    onConnectRef.current = onConnect
  }, [onConnect])

  useEffect(() => {
    const previousHandler = window.onTelegramAuth
    window.onTelegramAuth = (user) => {
      void onConnectRef.current(user).catch(() => undefined)
    }
    let cancelled = false
    void getTelegramWidgetConfig()
      .then((config) => {
        if (!cancelled) setBotUsername(config.bot_username.replace(/^@/, ''))
      })
      .catch(() => {
        if (!cancelled) setWidgetError('Telegram sign-in is temporarily unavailable.')
      })

    return () => {
      cancelled = true
      if (previousHandler) window.onTelegramAuth = previousHandler
      else delete window.onTelegramAuth
    }
  }, [])

  useEffect(() => {
    const mount = widgetRef.current
    if (!mount || !botUsername) return

    mount.replaceChildren()
    const script = document.createElement('script')
    script.async = true
    script.src = 'https://telegram.org/js/telegram-widget.js?22'
    script.dataset.telegramLogin = botUsername
    script.dataset.size = 'large'
    script.dataset.userpic = 'false'
    script.dataset.requestAccess = 'write'
    script.dataset.onauth = 'onTelegramAuth(user)'
    mount.append(script)

    return () => script.remove()
  }, [botUsername])

  return (
    <main className="telegram-page">
      <div className="telegram-shell">
        <header className="telegram-header">
          <button className="text-button" onClick={onBack} type="button">
            ← Back to workspace
          </button>
          <Brand />
        </header>

        <section className="telegram-layout">
          <div className="telegram-intro">
            <div className="empty-page-mark" aria-hidden="true">
              <Icon name="book" size={22} />
            </div>
            <div className="telegram-copy">
              <p className="telegram-kicker">Clinical messaging</p>
              <h1>Connect your Telegram account</h1>
              <p>
                Sign in with Telegram to link your account to DocPilot. Messages sent to the bot then use the same doctor identity and memory scope as this workspace.
              </p>
            </div>
          </div>

          <div className="telegram-connect-column">
            {error && <div className="form-alert" role="alert"><span>{error}</span></div>}
            {success && <div className="inline-alert success-alert" role="status"><span>{success}</span></div>}
            {widgetError && <p className="form-alert" role="alert">{widgetError}</p>}

            {!widgetError && !botUsername && <p role="status">Loading Telegram sign-in…</p>}
            <div aria-label="Sign in with Telegram" className="telegram-widget-mount" ref={widgetRef} />

            <div className="telegram-actions">
              {botUsername && (
                <a className="button-primary telegram-open-bot" href={`https://t.me/${botUsername}`} rel="noreferrer" target="_blank">
                  Open @{botUsername} in Telegram
                  <Icon name="arrow" size={16} />
                </a>
              )}
              <button
                className="text-button telegram-disconnect"
                disabled={busy}
                onClick={() => void onDisconnect()}
                type="button"
              >
                Disconnect
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
