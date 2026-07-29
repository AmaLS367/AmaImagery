import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

import { AuthFrame } from '../components/auth/AuthFrame'
import { Button } from '../components/ui/button'
import { requestPasswordReset } from '../lib/api'
import { appRoutes } from '../lib/routes'
import { cn } from '../lib/utils'
import { useAuth } from '../providers/AuthProvider'

type LoginProps = {
  initialMode?: 'login' | 'forgot'
}

export default function Login({ initialMode = 'login' }: LoginProps) {
  const navigate = useNavigate()
  const { login } = useAuth()

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

  const { register, handleSubmit, formState: { errors, isSubmitting }, reset } =
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
        await login({
          identifier: (data as LoginData).identifier,
          password: (data as LoginData).password,
        })
        setSuccess(true)
        navigate(appRoutes.generate)
      } else {
        await requestPasswordReset({ identifier: (data as ForgotData).identifier })
        setSuccess(true)
      }
    } catch (error) {
      setServerError(error instanceof Error ? error.message : mode === 'login' ? 'Sign-in failed.' : 'Could not send recovery email.')
    }
  }

  if (mode === 'forgot') {
    return (
      <AuthFrame
        eyebrow="Forgot password"
        title="Reset your password"
        note="Enter your email or username and we'll send you a recovery link."
        leftTitle="Reset access to your account."
        leftSubtitle="Enter the email or username tied to your account and the reset link will be sent there if the record exists."
        rightTitle="Password recovery"
        rightContent={
          <div className="space-y-5">
            <SurfaceCard title="Separate recovery page">
              Your recovery request is handled independently for security.
            </SurfaceCard>
          </div>
        }
        leftContent={
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
            <AuthField label="Email or username" hint="name@example.com" error={errors.identifier?.message}>
              <input
                id="identifier"
                type="text"
                autoComplete="username email"
                className="h-12 w-full rounded-2xl border border-border bg-secondary/50 px-4 text-foreground outline-none focus:border-primary/50 transition-colors dark:border-white/10 dark:bg-white/5 dark:text-white"
                {...register('identifier')}
              />
            </AuthField>

            {success ? <Alert tone="success">If that account exists, a reset link has been sent.</Alert> : null}
            {serverError ? <Alert tone="error">{serverError}</Alert> : null}

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Button type="submit" disabled={isSubmitting} size="lg" className="h-12 px-8 rounded-full font-bold">
                {isSubmitting ? 'Send reset link…' : 'Send reset link'}
              </Button>
              <Button asChild variant="ghost" className="rounded-full font-bold">
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
      title="Sign in to your account"
      note="Access your workspace, generation history, and personalized settings."
      leftTitle="Welcome back to AmaImagery Studio."
      leftSubtitle="Sign in to continue with generation, history, and your personalized settings."
      rightTitle="Why AmaImagery?"
      rightContent={
        <div className="space-y-5">
          <SurfaceCard title="Secure access">
            Full access to generation, history, and settings with secure authentication.
          </SurfaceCard>
          <SurfaceCard title="Forgot password?">
            Password recovery is available from the sign-in form below.
          </SurfaceCard>
        </div>
      }
      leftContent={
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
          {success ? <Alert tone="success">Sign-in succeeded. Redirecting to Generate.</Alert> : null}
          {serverError ? <Alert tone="error">{serverError}</Alert> : null}

          <AuthField label="Email or username" hint="name@example.com" error={errors.identifier?.message}>
            <input
              id="identifier"
              type="text"
              autoComplete="username email"
              className="h-12 w-full rounded-2xl border border-border bg-secondary/50 px-4 text-foreground outline-none focus:border-primary/50 transition-colors dark:border-white/10 dark:bg-white/5 dark:text-white"
              {...register('identifier')}
            />
          </AuthField>

          <AuthField label="Password" hint="••••••••" error={errors.password?.message}>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              className="h-12 w-full rounded-2xl border border-border bg-secondary/50 px-4 text-foreground outline-none focus:border-primary/50 transition-colors dark:border-white/10 dark:bg-white/5 dark:text-white"
              {...register('password')}
            />
          </AuthField>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button type="submit" disabled={isSubmitting} size="lg" className="h-12 px-8 rounded-full font-bold">
              {isSubmitting ? 'Sign in…' : 'Sign in'}
            </Button>
            <Button asChild variant="ghost" className="rounded-full font-bold">
              <Link to={appRoutes.forgotPassword}>Forgot password</Link>
            </Button>
          </div>

          <div className="flex flex-wrap gap-2 text-xs font-bold uppercase tracking-widest text-foreground/40 dark:text-white/40 pt-6 border-t border-border dark:border-white/10">
            <span>Secure session</span>
            <span>·</span>
            <Link to={appRoutes.register} className="text-primary hover:text-primary/80 transition-colors">
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
      <div className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">{label}</div>
      {children}
      <div className={cn(
        "text-xs font-medium",
        error ? "text-danger" : "text-foreground/40 dark:text-white/40"
      )}>
        {error || hint}
      </div>
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
