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
            <div className="telegram-intro-mark" aria-hidden="true">
              <Icon name="send" size={23} />
            </div>
            <div className="telegram-copy">
              <h1>Your workflow, now on Telegram.</h1>
              <p>
                Link the Telegram account you use for work. Messages sent to your DocPilot bot use the same doctor identity and memory scope as this workspace.
              </p>
            </div>
            <p className="telegram-trust-note">
              <Icon name="lock" size={17} />
              Telegram verifies your account before DocPilot links it to this workspace.
            </p>
          </div>

          <section aria-labelledby="telegram-connect-title" className="telegram-connect-panel">
            <div className="telegram-panel-heading">
              <h2 id="telegram-connect-title">Link your account</h2>
              <p>Two quick steps, then you can message your bot.</p>
            </div>

            {error && <div className="form-alert telegram-alert" role="alert"><span>{error}</span></div>}
            {success && <div className="inline-alert success-alert telegram-alert" role="status"><span>{success}</span></div>}
            {widgetError && <p className="form-alert telegram-alert" role="alert">{widgetError}</p>}

            <ol aria-label="Connect Telegram in two steps" className="telegram-steps">
              <li>
                <span aria-hidden="true" className="telegram-step-number">1</span>
                <div className="telegram-step-content">
                  <h3>Verify your Telegram account</h3>
                  <p>Use Telegram’s sign-in button to securely link this workspace.</p>
                  {!widgetError && !botUsername && (
                    <p className="telegram-widget-loading" role="status">Loading Telegram sign-in…</p>
                  )}
                  <div
                    aria-busy={busy}
                    aria-label="Sign in with Telegram"
                    className="telegram-widget-mount"
                    ref={widgetRef}
                    role="group"
                  />
                  {busy && <p className="telegram-linking" role="status">Linking your account…</p>}
                </div>
              </li>
              <li>
                <span aria-hidden="true" className="telegram-step-number">2</span>
                <div className="telegram-step-content">
                  <h3>Open your DocPilot bot</h3>
                  <p>Once linked, open the bot to start a conversation.</p>
                  {botUsername && (
                    <a
                      className="button-primary telegram-open-bot"
                      href={`https://t.me/${botUsername}`}
                      rel="noreferrer"
                      target="_blank"
                    >
                      Open @{botUsername} in Telegram
                      <Icon name="arrow" size={16} />
                    </a>
                  )}
                </div>
              </li>
            </ol>

            <div className="telegram-panel-footer">
              <button
                className="text-button telegram-disconnect"
                disabled={busy}
                onClick={() => void onDisconnect()}
                type="button"
              >
                Disconnect Telegram
              </button>
            </div>
          </section>
        </section>
      </div>
    </main>
  )
}
