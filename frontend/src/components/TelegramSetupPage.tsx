import { useState } from 'react'
import { Brand } from './Brand'
import { Icon } from './Icon'

interface TelegramSetupPageProps {
  busy: boolean
  error?: string
  success?: string
  onBack: () => void
  onConnect: (payload: { telegram_user_id: number; telegram_username?: string }) => Promise<void>
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
  const [telegramUserId, setTelegramUserId] = useState('')
  const [telegramUsername, setTelegramUsername] = useState('')

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const userId = Number(telegramUserId)
    if (!Number.isInteger(userId) || userId <= 0) {
      return
    }

    await onConnect({
      telegram_user_id: userId,
      telegram_username: telegramUsername.trim() || undefined,
    })
  }

  return (
    <main className="telegram-page">
      <div className="telegram-shell">
        <header className="telegram-header">
          <button className="text-button" onClick={onBack} type="button">
            ← Back to workspace
          </button>
          <Brand />
        </header>

        <section className="telegram-card">
          <div className="empty-page-mark" aria-hidden="true">
            <Icon name="lock" size={20} />
          </div>

          <div className="telegram-copy">
            <p className="telegram-kicker">Clinical messaging</p>
            <h1>Connect your Telegram bot</h1>
            <p>
              Link your Telegram account so bedside notes and quick clinical updates can be captured in your doctor memory workspace.
            </p>
          </div>

          <ol className="telegram-steps">
            <li>Open Telegram and start the DocPilot bot.</li>
            <li>Copy the numeric Telegram user ID from the bot response or from @userinfobot.</li>
            <li>Connect the account below to start sending bedside notes.</li>
          </ol>

          {error && (
            <div className="form-alert" role="alert">
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="inline-alert success-alert" role="status">
              <span>{success}</span>
            </div>
          )}

          <form className="telegram-form" onSubmit={handleSubmit}>
            <label className="field-label">
              Telegram user ID
              <input
                inputMode="numeric"
                onChange={(event) => setTelegramUserId(event.target.value)}
                placeholder="123456789"
                type="number"
                value={telegramUserId}
              />
            </label>

            <label className="field-label">
              Telegram username (optional)
              <input
                onChange={(event) => setTelegramUsername(event.target.value)}
                placeholder="dr_smith"
                type="text"
                value={telegramUsername}
              />
            </label>

            <div className="telegram-actions">
              <button className="button-primary auth-submit" disabled={busy} type="submit">
                {busy ? 'Connecting…' : 'Connect Telegram'}
              </button>
              <button
                className="text-button telegram-disconnect"
                disabled={busy}
                onClick={() => void onDisconnect()}
                type="button"
              >
                Disconnect
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  )
}
