import { useState } from 'react'
import type { FormEvent } from 'react'
import { Brand } from './Brand'
import { Icon } from './Icon'

interface AuthScreenProps {
  mode: 'login' | 'register'
  busy: boolean
  error: string
  onNavigate: (path: string) => void
  onSubmit: (credentials: { name?: string; email: string; password: string }) => Promise<void>
}

export function AuthScreen({ mode, busy, error, onNavigate, onSubmit }: AuthScreenProps) {
  const isRegister = mode === 'register'
  const [showPassword, setShowPassword] = useState(false)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const name = String(formData.get('name') ?? '').trim()
    const email = String(formData.get('email') ?? '').trim()
    const password = String(formData.get('password') ?? '')
    void onSubmit({ ...(isRegister ? { name } : {}), email, password })
  }

  return (
    <main className="auth-layout">
      <section className="auth-intro" aria-label="About DocPilot">
        <Brand inverse />
        <div className="auth-intro-copy">
          <p className="auth-intro-line">Your clinical memory, in conversation.</p>
          <h1>Keep the details you’ve documented close at hand.</h1>
          <p className="auth-intro-description">
            Ask naturally, capture a visit, and return to the context you’ve already saved.
          </p>
        </div>
        <div className="auth-principles">
          <p><span aria-hidden="true" />Grounded in documented memories</p>
          <p><span aria-hidden="true" />Your conversations, ready to revisit</p>
          <p><span aria-hidden="true" />Made for doctors, not patients</p>
        </div>
        <span className="auth-page-mark" aria-hidden="true">
          <Icon name="book" size={62} />
        </span>
      </section>

      <section className="auth-form-panel">
        <div className="auth-form-wrap">
          <div className="auth-mobile-brand"><Brand /></div>
          <h2>{isRegister ? 'Create your account' : 'Welcome back'}</h2>
          <p className="auth-form-intro">
            {isRegister
              ? 'Set up your private doctor account to begin.'
              : 'Sign in to continue to your clinical memory.'}
          </p>

          {error && <p className="form-alert" role="alert">{error}</p>}

          <form className="auth-form" onSubmit={handleSubmit}>
            {isRegister && (
              <label className="field-label">
                Name
                <input
                  autoComplete="name"
                  name="name"
                  placeholder="Your name"
                  required
                  type="text"
                />
              </label>
            )}
            <label className="field-label">
              Email
              <input
                autoComplete="email"
                name="email"
                placeholder="you@clinic.com"
                required
                type="email"
              />
            </label>
            <label className="field-label">
              Password
              <span className="password-input-wrap">
                <input
                  autoComplete={isRegister ? 'new-password' : 'current-password'}
                  minLength={8}
                  name="password"
                  placeholder={isRegister ? 'At least 8 characters' : 'Your password'}
                  required
                  type={showPassword ? 'text' : 'password'}
                />
                <button
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  aria-pressed={showPassword}
                  className="password-visibility-button"
                  onClick={() => setShowPassword((visible) => !visible)}
                  title={showPassword ? 'Hide password' : 'Show password'}
                  type="button"
                >
                  <Icon name={showPassword ? 'eyeOff' : 'eye'} size={19} />
                </button>
              </span>
            </label>
            <button className="button-primary auth-submit" disabled={busy} type="submit">
              {busy ? 'Please wait…' : isRegister ? 'Create account' : 'Sign in'}
              {!busy && <Icon name="arrow" size={17} />}
            </button>
          </form>

          <p className="auth-switch">
            {isRegister ? 'Already have an account?' : 'New to DocPilot?'}
            <button
              className="text-button"
              onClick={() => onNavigate(isRegister ? '/login' : '/register')}
              type="button"
            >
              {isRegister ? 'Sign in' : 'Create an account'}
            </button>
          </p>

          <p className="auth-privacy">
            <Icon name="lock" size={15} />
            Your account is private to you.
          </p>
          <p className="auth-safety">
            DocPilot recalls documented information. It does not diagnose or recommend treatment.
          </p>
        </div>
      </section>
    </main>
  )
}
