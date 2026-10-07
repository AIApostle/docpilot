import { useState } from 'react'
import type { FormEvent } from 'react'
import { Brand } from './Brand'
import { Icon } from './Icon'
import { ui } from '../ui'

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
    <main className={ui.authLayout}>
      <section className={ui.authIntro} aria-label="About DocPilot">
        <Brand inverse />
        <div className={ui.authCopy}>
          <p className={ui.authKicker}>Your clinical memory, in conversation.</p>
          <h1 className={ui.authTitle}>Keep the details you’ve documented close at hand.</h1>
          <p className={ui.authDescription}>
            Ask naturally, capture a visit, and return to the context you’ve already saved.
          </p>
        </div>
        <div className={ui.authPrinciples}>
          <p className={ui.authPrinciple}><span className={ui.authDot} aria-hidden="true" />Grounded in documented memories</p>
          <p className={ui.authPrinciple}><span className={ui.authDot} aria-hidden="true" />Your conversations, ready to revisit</p>
          <p className={ui.authPrinciple}><span className={ui.authDot} aria-hidden="true" />Made for doctors, not patients</p>
        </div>
        <span className={ui.authPageMark} aria-hidden="true">
          <Icon name="book" size={62} />
        </span>
      </section>

      <section className={ui.authFormPanel}>
        <div className={ui.authFormWrap}>
          <div className={ui.authMobileBrand}><Brand /></div>
          <h2 className={ui.authHeading}>{isRegister ? 'Create your account' : 'Welcome back'}</h2>
          <p className={ui.authFormIntro}>
            {isRegister
              ? 'Set up your private doctor account to begin.'
              : 'Sign in to continue to your clinical memory.'}
          </p>

          {error && <p className={ui.formAlert} role="alert">{error}</p>}

          <form className={ui.authForm} onSubmit={handleSubmit}>
            {isRegister && (
              <label className={ui.fieldLabel}>
                Name
                <input
                  className={ui.fieldInput}
                  autoComplete="name"
                  name="name"
                  placeholder="Your name"
                  required
                  type="text"
                />
              </label>
            )}
            <label className={ui.fieldLabel}>
              Email
              <input
                className={ui.fieldInput}
                autoComplete="email"
                name="email"
                placeholder="you@clinic.com"
                required
                type="email"
              />
            </label>
            <label className={ui.fieldLabel}>
              Password
              <span className={ui.passwordWrap}>
                <input
                  className={`${ui.fieldInput} pr-12`}
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
                  className={ui.passwordButton}
                  onClick={() => setShowPassword((visible) => !visible)}
                  title={showPassword ? 'Hide password' : 'Show password'}
                  type="button"
                >
                  <Icon name={showPassword ? 'eyeOff' : 'eye'} size={19} />
                </button>
              </span>
            </label>
            <button className={ui.primaryButton} disabled={busy} type="submit">
              {busy ? 'Please wait…' : isRegister ? 'Create account' : 'Sign in'}
              {!busy && <Icon name="arrow" size={17} />}
            </button>
          </form>

          <p className={ui.authSwitch}>
            {isRegister ? 'Already have an account?' : 'New to DocPilot?'}
            <button
              className={ui.textButton}
              onClick={() => onNavigate(isRegister ? '/login' : '/register')}
              type="button"
            >
              {isRegister ? 'Sign in' : 'Create an account'}
            </button>
          </p>

          <p className={ui.authPrivacy}>
            <Icon name="lock" size={15} />
            Your account is private to you.
          </p>
          <p className={ui.authSafety}>
            DocPilot recalls documented information. It does not diagnose or recommend treatment.
          </p>
        </div>
      </section>
    </main>
  )
}
