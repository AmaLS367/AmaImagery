import { useState } from 'react'
import { Link } from 'react-router-dom'

import { AuthFrame } from '../components/auth/AuthFrame'
import { Button } from '../components/ui/button'
import { appRoutes } from '../lib/routes'

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
      const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier: identifier.trim() }),
      })
      if (!response.ok && response.status !== 204) {
        throw new Error((await response.text().catch(() => '')) || `HTTP ${response.status}`)
      }
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
      title="Single-task recovery request page with success confirmation"
      note="Recovery is a dedicated page, not a hidden alternate mode inside login."
      leftTitle="Reset access without mixing auth states."
      leftSubtitle="Enter the email or username connected to your account. If the account exists, a reset link will be sent."
      rightTitle={success ? 'Forgot Password / Success / Light' : 'Forgot Password / Default / Dark'}
      rightContent={
        <SurfaceCard title={success ? 'Reset link sent' : 'Recovery path'}>
          {success
            ? 'Check your inbox for the secure link to update your password and continue back to AmaImagery.'
            : 'The request stays single-purpose, with its own success confirmation instead of hiding inside login.'}
        </SurfaceCard>
      }
      leftContent={
        <form onSubmit={onSubmit} className="space-y-5" noValidate>
          {error ? <Alert tone="error">{error}</Alert> : null}
          {success ? <Alert tone="success">If that account exists, the reset link has been sent.</Alert> : null}

          <AuthField label="Email or username" hint="name@example.com">
            <input
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
              type="text"
              autoComplete="username email"
              className="h-12 w-full rounded-[18px] border border-white/10 bg-white/[0.03] px-4 text-white outline-none focus:border-primary/50"
            />
          </AuthField>

          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Send reset link…' : 'Send reset link'}
            </Button>
            <Button asChild variant="ghost">
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
      <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/58">{label}</div>
      {children}
      <div className="text-xs text-white/42">{hint}</div>
    </label>
  )
}

function SurfaceCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[24px] border border-white/6 bg-white/[0.02] p-5">
      <div className="font-display text-[28px] font-semibold tracking-[-0.05em] text-white">{title}</div>
      <p className="mt-3 text-sm leading-6 text-white/55">{children}</p>
    </div>
  )
}

function Alert({ tone, children }: { tone: 'success' | 'error'; children: React.ReactNode }) {
  return (
    <div
      className={[
        'rounded-[18px] border px-4 py-3 text-sm',
        tone === 'success'
          ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-200'
          : 'border-red-500/25 bg-red-500/10 text-red-200',
      ].join(' ')}
    >
      {children}
    </div>
  )
}
