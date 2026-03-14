import { useState } from 'react'
import { Link } from 'react-router-dom'

import { AuthFrame } from '../components/auth/AuthFrame'
import { Button } from '../components/ui/button'
import { requestPasswordReset } from '../lib/api'
import { appRoutes } from '../lib/routes'
import { cn } from '../lib/utils'

export default function ForgotPassword() {
  const [identifier, setIdentifier] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    setSuccess(false)

    if (!identifier.trim()) {
      setError('Email or username is required.')
      return
    }

    setSubmitting(true)
    try {
      await requestPasswordReset({ identifier: identifier.trim() })
      setSuccess(true)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not send recovery email.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthFrame
      eyebrow="Forgot password"
      title="Reset your password"
      note="Enter your email or username to receive a password reset link."
      leftTitle="Recover access to your account."
      leftSubtitle="Enter the email or username connected to your account. If the account exists, a reset link will be sent."
      rightTitle={success ? 'Link sent' : 'Password recovery'}
      rightContent={
        <SurfaceCard title={success ? 'Reset link sent' : 'How it works'}>
          {success
            ? 'Check your inbox for the secure link to update your password and continue back to AmaImagery.'
            : 'Enter your email or username and we will send you a secure link to reset your password.'}
        </SurfaceCard>
      }
      leftContent={
        <form onSubmit={onSubmit} className="space-y-6" noValidate>
          {error ? <Alert tone="error">{error}</Alert> : null}
          {success ? <Alert tone="success">If that account exists, the reset link has been sent.</Alert> : null}

          <AuthField label="Email or username" hint="name@example.com">
            <input
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
              type="text"
              autoComplete="username email"
              className="h-12 w-full rounded-2xl border border-border bg-secondary/50 px-4 text-foreground outline-none focus:border-primary/50 transition-colors dark:border-white/10 dark:bg-white/5 dark:text-white"
            />
          </AuthField>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button type="submit" disabled={submitting} size="lg" className="h-12 px-8 rounded-full font-bold">
              {submitting ? 'Send reset link…' : 'Send reset link'}
            </Button>
            <Button asChild variant="ghost" className="rounded-full font-bold">
              <Link to={appRoutes.login}>Back to sign in</Link>
            </Button>
          </div>
        </form>
      }
    />
  )
}

function AuthField({
  label,
  hint,
  children,
}: {
  label: string
  hint: string
  children: React.ReactNode
}) {
  return (
    <label className="block space-y-2">
      <div className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">{label}</div>
      {children}
      <div className="text-xs font-medium text-foreground/40 dark:text-white/40">{hint}</div>
    </label>
  )
}

function SurfaceCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[32px] border border-border bg-secondary/30 p-6 space-y-3 dark:border-white/10 dark:bg-white/5">
      <div className="font-display text-2xl font-bold tracking-tight text-foreground dark:text-white">{title}</div>
      <p className="text-sm leading-relaxed text-foreground/60 dark:text-white/60 font-medium">{children}</p>
    </div>
  )
}

function Alert({ tone, children }: { tone: 'success' | 'error'; children: React.ReactNode }) {
  return (
    <div
      className={cn(
        "rounded-2xl border px-4 py-3 text-sm font-bold",
        tone === 'success'
          ? 'border-success/20 bg-success/10 text-success'
          : 'border-danger/20 bg-danger/10 text-danger',
      )}
    >
      {children}
    </div>
  )
}
