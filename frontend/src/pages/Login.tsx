import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

import { AuthFrame } from '../components/auth/AuthFrame'
import { Button } from '../components/ui/button'
import { appRoutes } from '../lib/routes'

type LoginProps = {
  initialMode?: 'login' | 'forgot'
}

export default function Login({ initialMode = 'login' }: LoginProps) {
  const navigate = useNavigate()

  type LoginData = { identifier: string; password: string }
  type ForgotData = { identifier: string }
  type FormValues = { identifier: string; password?: string }

  const schemaLogin = z.object({
    identifier: z.string().min(2, 'Email or username is required.'),
    password: z.string().min(8, 'Password must contain at least 8 characters.'),
  })
  const schemaForgot = z.object({
    identifier: z.string().min(2, 'Email or username is required.'),
  })

  const [serverError, setServerError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [mode, setMode] = useState<'login' | 'forgot'>(initialMode)

  const { register, handleSubmit, formState: { errors, isSubmitting }, watch, reset } =
    useForm<FormValues>({ resolver: zodResolver(mode === 'login' ? schemaLogin : schemaForgot), mode: 'onChange' })


  useEffect(() => {
    setMode(initialMode)
  }, [initialMode])

  useEffect(() => {
    reset({ identifier: '', ...(mode === 'login' ? { password: '' } : {}) })
    setServerError(null)
    setSuccess(false)
  }, [mode, reset])

  const onSubmit = async (data: FormValues) => {
    setServerError(null)
    setSuccess(false)
    try {
      if (mode === 'login') {
        const res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ identifier: (data as LoginData).identifier, password: (data as LoginData).password }),
        })
        if (!res.ok) throw new Error((await res.text().catch(() => '')) || `Ошибка ${res.status}`)
        const payload = await res.json().catch(() => null)
        
        // Clear old tokens first
        try { 
          localStorage.removeItem('auth')
          localStorage.removeItem('access_token')
        } catch {}
        
        // Save new tokens properly
        try { 
          localStorage.setItem('auth', JSON.stringify({ loggedIn: true, user: payload }))
          // Also save access token separately for compatibility
          if (payload?.access_token) {
            localStorage.setItem('access_token', payload.access_token)
          }
        } catch {}
        
        window.dispatchEvent(new CustomEvent('auth:update'))
        setSuccess(true)
        navigate(appRoutes.generate)
      } else {
        const res = await fetch('/api/v1/auth/forgot-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ identifier: (data as ForgotData).identifier }),
        })
        if (!res.ok && res.status !== 204) throw new Error((await res.text().catch(() => '')) || `HTTP ${res.status}`)
        setSuccess(true) // «Если такой аккаунт есть — письмо отправлено»
      }
    } catch (e: any) {
      setServerError(e?.message || (mode === 'login' ? 'Sign-in failed.' : 'Could not send recovery email.'))
    }
  }

  if (mode === 'forgot') {
    return (
      <AuthFrame
        eyebrow="Forgot password"
        title="Password recovery lives on its own route."
        note="Recovery remains separate from login so the sign-in page does not collapse multiple auth jobs into one canvas."
        leftTitle="Reset access without losing the rest of the auth flow."
        leftSubtitle="Enter the email or username tied to your account and the reset link will be sent there if the record exists."
        rightTitle="Recovery / Light"
        rightContent={
          <div className="space-y-5">
            <SurfaceCard title="Dedicated recovery path">
              Forgot password is a separate destination, not an inline mode hidden inside login.
            </SurfaceCard>
          </div>
        }
        leftContent={
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <AuthField label="Email or username" hint="name@example.com" error={errors.identifier?.message}>
              <input
                id="identifier"
                type="text"
                autoComplete="username email"
                className="h-12 w-full rounded-[18px] border border-white/10 bg-white/[0.03] px-4 text-white outline-none focus:border-primary/50"
                {...register('identifier')}
              />
            </AuthField>

            {success ? <Alert tone="success">If that account exists, a reset link has been sent.</Alert> : null}
            {serverError ? <Alert tone="error">{serverError}</Alert> : null}

            <div className="flex flex-wrap items-center gap-3">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Send reset link…' : 'Send reset link'}
              </Button>
              <Button asChild variant="ghost">
                <Link to={appRoutes.login}>Back to login</Link>
              </Button>
            </div>
          </form>
        }
      />
    )
  }

  return (
    <AuthFrame
      eyebrow="Login"
      title="Dedicated sign-in page with recovery and register routes"
      note="No shared auth board. Login is its own page with dark and light variants inside this container."
      leftTitle="Welcome back to AmaImagery Studio."
      leftSubtitle="Sign in to continue with generation, history, and your personalized shell settings."
      rightTitle="Login / Light"
      rightContent={
        <div className="space-y-5">
          <SurfaceCard title="Trust line">
            Clear access to generation, history, and settings with no mixed-purpose auth canvas.
          </SurfaceCard>
          <SurfaceCard title="Recovery path">
            Forgot password is a separate destination, not an inline mode hidden inside login.
          </SurfaceCard>
        </div>
      }
      leftContent={
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
          {success ? <Alert tone="success">Sign-in succeeded. Redirecting to Generate.</Alert> : null}
          {serverError ? <Alert tone="error">{serverError}</Alert> : null}

          <AuthField label="Email or username" hint="name@example.com" error={errors.identifier?.message}>
            <input
              id="identifier"
              type="text"
              autoComplete="username email"
              className="h-12 w-full rounded-[18px] border border-white/10 bg-white/[0.03] px-4 text-white outline-none focus:border-primary/50"
              {...register('identifier')}
            />
          </AuthField>

          <AuthField label="Password" hint="••••••••" error={errors.password?.message}>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              className="h-12 w-full rounded-[18px] border border-white/10 bg-white/[0.03] px-4 text-white outline-none focus:border-primary/50"
              {...register('password')}
            />
          </AuthField>

          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Sign in…' : 'Sign in'}
            </Button>
            <Button asChild variant="ghost">
              <Link to={appRoutes.forgotPassword}>Forgot password</Link>
            </Button>
          </div>

          <div className="flex flex-wrap gap-2 text-sm text-white/50">
            <span>Protected session</span>
            <span>·</span>
            <span>runtime-aware auth</span>
            <span>·</span>
            <Link to={appRoutes.register} className="text-white/78 hover:text-white">
              Create account
            </Link>
          </div>
        </form>
      }
    />
  )
}

function AuthField({
  label,
  hint,
  error,
  children,
}: {
  label: string
  hint: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <label className="block space-y-2">
      <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/58">{label}</div>
      {children}
      <div className={error ? 'text-xs text-red-300' : 'text-xs text-white/42'}>{error || hint}</div>
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
