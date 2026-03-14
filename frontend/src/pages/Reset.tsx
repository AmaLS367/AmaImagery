import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ShieldCheck, ArrowRight } from 'lucide-react'

import { AuthFrame } from '../components/auth/AuthFrame'
import { Button } from '../components/ui/button'
import { resetPasswordRequest } from '../lib/api'
import { appRoutes } from '../lib/routes'
import { cn } from '../lib/utils'

export default function Reset() {
  const navigate = useNavigate()
  const [pwd1, setPwd1] = useState('')
  const [pwd2, setPwd2] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [invalidToken, setInvalidToken] = useState(false)

  const token = useMemo(() => {
    try {
      return new URLSearchParams(window.location.search).get('token') || ''
    } catch {
      return ''
    }
  }, [])

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (submitting) return
    setError(null)
    setInvalidToken(false)

    if (!token) {
      setInvalidToken(true)
      return
    }
    if (pwd1.length < 8) {
      setError('Password must contain at least 8 characters.')
      return
    }
    if (pwd1 !== pwd2) {
      setError('Passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      await resetPasswordRequest({ token, new_password: pwd1 })
      setSuccess(true)
      setTimeout(() => navigate(appRoutes.login), 1500)
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : 'Reset could not be completed.'
      if (/invalid|expired/i.test(message)) {
        setInvalidToken(true)
      }
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  if (invalidToken) {
    return (
      <AuthFrame
        eyebrow="Reset password"
        title="Invalid or expired link"
        note="For security, password reset links expire after a short period."
        leftTitle="Link no longer valid."
        leftSubtitle="The link you used is broken or has expired. Please request a new one to continue."
        rightTitle="Request access"
        rightContent={
          <div className="space-y-5">
            <SurfaceCard title="Secure Links">
              Each link is generated uniquely for your account and limited by time.
            </SurfaceCard>
          </div>
        }
        leftContent={
          <div className="space-y-6">
            <Button asChild size="lg" className="h-12 px-8 rounded-full font-bold">
              <Link to={appRoutes.forgotPassword}>Request new link</Link>
            </Button>
            <Button asChild variant="ghost" className="rounded-full font-bold">
              <Link to={appRoutes.login}>Back to login</Link>
            </Button>
          </div>
        }
      />
    )
  }

  return (
    <AuthFrame
      eyebrow="Reset password"
      title="Create your new password"
      note="Set a new password for your account to regain access to the studio."
      leftTitle={success ? "Password updated." : "Set your new password."}
      leftSubtitle={success 
        ? "Your password has been successfully reset. Redirecting you to the login page." 
        : "Choose a strong password that you haven't used before."}
      rightTitle="Security"
      rightContent={
        <div className="space-y-5">
          <SurfaceCard title="Strong Passwords">
            We recommend using at least 8 characters with a mix of letters and numbers.
          </SurfaceCard>
        </div>
      }
      leftContent={
        success ? (
          <Alert tone="success">Success! Your password is now updated.</Alert>
        ) : (
          <form onSubmit={onSubmit} className="space-y-6" noValidate>
            {error ? <Alert tone="error">{error}</Alert> : null}

            <AuthField label="New password" hint="Minimum 8 characters">
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                value={pwd1}
                onChange={(event) => setPwd1(event.target.value)}
                className="h-12 w-full rounded-2xl border border-border bg-secondary/50 px-4 text-foreground outline-none focus:border-primary/50 transition-colors dark:border-white/10 dark:bg-white/5 dark:text-white"
              />
            </AuthField>

            <AuthField label="Confirm password" hint="Repeat the same password">
              <input
                id="password_confirm"
                type="password"
                autoComplete="new-password"
                value={pwd2}
                onChange={(event) => setPwd2(event.target.value)}
                className="h-12 w-full rounded-2xl border border-border bg-secondary/50 px-4 text-foreground outline-none focus:border-primary/50 transition-colors dark:border-white/10 dark:bg-white/5 dark:text-white"
              />
            </AuthField>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Button type="submit" disabled={submitting} size="lg" className="h-12 px-8 rounded-full font-bold">
                {submitting ? 'Updating…' : 'Update password'}
              </Button>
              <Button asChild variant="ghost" className="rounded-full font-bold">
                <Link to={appRoutes.login}>Cancel</Link>
              </Button>
            </div>
          </form>
        )
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
