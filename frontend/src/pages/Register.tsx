import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

import { AuthFrame } from '../components/auth/AuthFrame'
import { Button } from '../components/ui/button'
import { appRoutes } from '../lib/routes'

export default function Register() {
  const navigate = useNavigate()

  type FormData = {
    email: string
    username: string
    password: string
    confirm: string
    agree?: boolean
  }

  const schema = z.object({
    email: z.string().min(1, 'Email is required.').email('Enter a valid email address.'),
    username: z.string().min(2, 'Username is required.'),
    password: z.string().min(8, 'Password must contain at least 8 characters.'),
    confirm: z.string().min(8, 'Repeat the password.'),
    agree: z.boolean().optional()
  }).refine((v) => v.password === v.confirm, {
    message: 'Passwords do not match.',
    path: ['confirm']
  })

  const [serverError, setServerError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<FormData>({ resolver: zodResolver(schema), mode: 'onChange' })

  const onSubmit = async (data: FormData) => {
    setServerError(null)
    setSuccess(false)
    try {
      const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: data.email, password: data.password, username: data.username }),
      })
      if (!res.ok) {
        const text = await res.text().catch(() => '')
        throw new Error(text || `HTTP ${res.status}`)
      }
      const payload = await res.json().catch(() => null)
  
      // Помечаем пользователя как вошедшего, чтобы топбар переключился
      try { 
        localStorage.setItem('auth', JSON.stringify({ loggedIn: true, user: payload }))
        if (payload?.access_token) {
          localStorage.setItem('access_token', payload.access_token)
        }
      } catch {}
      window.dispatchEvent(new CustomEvent('auth:update'))
  
      setSuccess(true)
      reset({ username: '', email: '', password: '', confirm: '' })
      navigate(appRoutes.generate)
    } catch (e: any) {
      setServerError(e?.message || 'Registration failed.')
    }
  }  

  return (
    <AuthFrame
      eyebrow="Register"
      title="Account creation page with policy acknowledgment and clear handoff to sign-in"
      note="Production-facing English copy only. No inline dev placeholders."
      leftTitle="Create an account for guided generation and saved history."
      leftSubtitle="Simple credential creation without collapsing login, recovery, and reset into a single auth canvas."
      rightTitle="Register / Light"
      rightContent={
        <SurfaceCard title="Clean onboarding">
          Simple credential creation without collapsing login, recovery, and reset into a single auth canvas.
        </SurfaceCard>
      }
      leftContent={
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
          {success ? <Alert tone="success">Account created. Redirecting to Generate.</Alert> : null}
          {serverError ? <Alert tone="error">{serverError}</Alert> : null}

          <div className="grid gap-5 sm:grid-cols-2">
            <AuthField label="Username" hint="studio_operator" error={errors.username?.message}>
              <input
                id="username"
                type="text"
                autoComplete="username"
                className="h-12 w-full rounded-[18px] border border-white/10 bg-white/[0.03] px-4 text-white outline-none focus:border-primary/50"
                {...register('username')}
              />
            </AuthField>

            <AuthField label="Email" hint="name@example.com" error={errors.email?.message}>
              <input
                id="email"
                type="email"
                autoComplete="email"
                className="h-12 w-full rounded-[18px] border border-white/10 bg-white/[0.03] px-4 text-white outline-none focus:border-primary/50"
                {...register('email')}
              />
            </AuthField>

            <AuthField label="Password" hint="At least 8 characters" error={errors.password?.message}>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                className="h-12 w-full rounded-[18px] border border-white/10 bg-white/[0.03] px-4 text-white outline-none focus:border-primary/50"
                {...register('password')}
              />
            </AuthField>

            <AuthField label="Confirm password" hint="Repeat password" error={errors.confirm?.message}>
              <input
                id="confirm"
                type="password"
                autoComplete="new-password"
                className="h-12 w-full rounded-[18px] border border-white/10 bg-white/[0.03] px-4 text-white outline-none focus:border-primary/50"
                {...register('confirm')}
              />
            </AuthField>
          </div>

          <div className="space-y-2 text-sm text-white/62">
            <p className="font-semibold text-white/86">
              By creating an account, you agree to the service rules and privacy policy.
            </p>
            <p>The note stays concise and product-facing.</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Create account…' : 'Create account'}
            </Button>
            <Button asChild variant="ghost">
              <Link to={appRoutes.login}>Already have an account?</Link>
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
