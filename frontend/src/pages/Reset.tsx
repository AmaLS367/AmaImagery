import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/button'
import { SectionEyebrow, SurfacePanel } from '../components/ui/foundation'
import { appRoutes } from '../lib/routes'

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
      const response = await fetch('/api/v1/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: pwd1 }),
      })

      if (!response.ok) {
        setInvalidToken(response.status >= 400)
        throw new Error((await response.text().catch(() => '')) || `HTTP ${response.status}`)
      }

      setSuccess(true)
      setTimeout(() => navigate(appRoutes.login), 1200)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Reset could not be completed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="page-shell space-y-6 py-8 xl:py-10">
      <SurfacePanel className="overflow-hidden rounded-[40px] bg-[#050910] text-white">
        <div className="grid gap-4 border-b border-white/8 px-5 py-5 md:px-8 md:py-6 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-2">
            <SectionEyebrow>Reset password</SectionEyebrow>
            <h1 className="font-display text-3xl font-semibold tracking-[-0.05em] text-white sm:text-4xl">
              Reset page with valid token, invalid token, and success states
            </h1>
          </div>
          <div className="text-sm leading-6 text-white/48 xl:pl-12 xl:text-right">
            Clear recovery and return-to-login path with no state mixing across pages.
          </div>
        </div>

        <div className="space-y-6 p-5 md:p-8">
          <div className="grid gap-6 xl:grid-cols-2">
            <div className="rounded-[32px] border border-white/6 bg-white/[0.02] p-6 md:p-8">
              <div className="space-y-2">
                <div className="text-sm font-semibold text-white">Reset Password / Valid Token / Dark</div>
                <p className="text-sm leading-6 text-white/55">Set a new password and return to sign in.</p>
              </div>

              <form onSubmit={onSubmit} className="mt-8 space-y-5" noValidate>
                {error ? <Alert tone="error">{error}</Alert> : null}

                <AuthField label="New password" hint="••••••••">
                  <input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    value={pwd1}
                    onChange={(event) => setPwd1(event.target.value)}
                    className="h-12 w-full rounded-[18px] border border-white/10 bg-white/[0.03] px-4 text-white outline-none focus:border-primary/50"
                  />
                </AuthField>

                <AuthField label="Confirm password" hint="••••••••">
                  <input
                    id="password_confirm"
                    type="password"
                    autoComplete="new-password"
                    value={pwd2}
                    onChange={(event) => setPwd2(event.target.value)}
                    className="h-12 w-full rounded-[18px] border border-white/10 bg-white/[0.03] px-4 text-white outline-none focus:border-primary/50"
                  />
                </AuthField>

                <Button type="submit" disabled={submitting}>
                  {submitting ? 'Update password…' : 'Update password'}
                </Button>
              </form>
            </div>

            <div className="rounded-[32px] border border-white/6 bg-white/[0.02] p-6 md:p-8">
              <div className="space-y-2">
                <div className="text-sm font-semibold text-white">Reset Password / Invalid Token / Dark</div>
                <p className="text-sm leading-6 text-white/55">Expired or broken reset link.</p>
              </div>
              <div className="mt-8 rounded-[24px] border border-white/6 bg-white/[0.02] p-5">
                <div className="font-display text-[28px] font-semibold tracking-[-0.05em] text-white">
                  This reset link is no longer valid.
                </div>
                <p className="mt-3 text-sm leading-6 text-white/55">
                  Request a new link and try again. Existing password remains unchanged.
                </p>
                <Button asChild variant="secondary" className="mt-5">
                  <Link to={appRoutes.forgotPassword}>Request new link</Link>
                </Button>
              </div>
            </div>
          </div>

          <div className="h-px bg-gradient-to-r from-transparent via-primary/70 to-transparent" />

          <div className="max-w-[560px] rounded-[32px] border border-white/6 bg-white/[0.02] p-6 md:p-8">
            <div className="space-y-2">
              <div className="text-sm font-semibold text-white">Reset Password / Success / Light</div>
              <p className="text-sm leading-6 text-white/55">Password updated.</p>
            </div>
            <div className="mt-4 rounded-[24px] border border-white/6 bg-white/[0.02] p-5">
              <div className="font-semibold text-white">Your password has been updated.</div>
              <p className="mt-2 text-sm leading-6 text-white/55">Return to sign in and continue to the app.</p>
            </div>
            <Button asChild className="mt-5 w-full">
              <Link to={appRoutes.login}>Back to sign in</Link>
            </Button>
          </div>
        </div>
      </SurfacePanel>
    </section>
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
