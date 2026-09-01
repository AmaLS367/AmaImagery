import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

import { AuthFrame } from '../components/auth/AuthFrame'
import { Button } from '../components/ui/button'
import { appRoutes } from '../lib/routes'
import { cn } from '../lib/utils'
import { useAuth } from '../providers/AuthProvider'

export default function Register() {
  const navigate = useNavigate()
  const { register: registerAccount } = useAuth()

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
      await registerAccount({
        email: data.email,
        password: data.password,
        username: data.username,
      })
      setSuccess(true)
      reset({ username: '', email: '', password: '', confirm: '' })
      navigate(appRoutes.generate)
    } catch (error) {
      setServerError(error instanceof Error ? error.message : 'Registration failed.')
    }
  }

  return (
    <AuthFrame
      eyebrow="Register"
      title="Create your account"
      note="Sign up to start generating images, save your history, and customize your workspace."
      leftTitle="Join AmaImagery Studio."
      leftSubtitle="Create your account with a few simple steps and get started right away."
      rightTitle="Get started"
      rightContent={
        <div className="space-y-5">
          <SurfaceCard title="Simple setup">
            Quick account creation with instant access to all features.
          </SurfaceCard>
          <SurfaceCard title="Data Privacy">
            Your data is handled according to our strictly professional privacy policy.
          </SurfaceCard>
        </div>
      }
      leftContent={
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
          {success ? <Alert tone="success">Account created. Redirecting to Generate.</Alert> : null}
          {serverError ? <Alert tone="error">{serverError}</Alert> : null}

          <div className="grid gap-6 sm:grid-cols-2">
            <AuthField label="Username" hint="studio_operator" error={errors.username?.message}>
              <input
                id="username"
                type="text"
                autoComplete="username"
                className="h-12 w-full rounded-2xl border border-border bg-secondary/50 px-4 text-foreground outline-none focus:border-primary/50 transition-colors dark:border-white/10 dark:bg-white/5 dark:text-white"
                {...register('username')}
              />
            </AuthField>

            <AuthField label="Email" hint="name@example.com" error={errors.email?.message}>
              <input
                id="email"
                type="email"
                autoComplete="email"
                className="h-12 w-full rounded-2xl border border-border bg-secondary/50 px-4 text-foreground outline-none focus:border-primary/50 transition-colors dark:border-white/10 dark:bg-white/5 dark:text-white"
                {...register('email')}
              />
            </AuthField>

            <AuthField label="Password" hint="At least 8 characters" error={errors.password?.message}>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                className="h-12 w-full rounded-2xl border border-border bg-secondary/50 px-4 text-foreground outline-none focus:border-primary/50 transition-colors dark:border-white/10 dark:bg-white/5 dark:text-white"
                {...register('password')}
              />
            </AuthField>

            <AuthField label="Confirm password" hint="Repeat password" error={errors.confirm?.message}>
              <input
                id="confirm"
                type="password"
                autoComplete="new-password"
                className="h-12 w-full rounded-2xl border border-border bg-secondary/50 px-4 text-foreground outline-none focus:border-primary/50 transition-colors dark:border-white/10 dark:bg-white/5 dark:text-white"
                {...register('confirm')}
              />
            </AuthField>
          </div>

          <div className="space-y-2 text-sm font-medium text-foreground/60 dark:text-white/60">
            <p className="font-bold text-foreground dark:text-white">
              By creating an account, you agree to the service rules and privacy policy.
            </p>
            <p>Your data is handled according to our privacy policy.</p>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button type="submit" disabled={isSubmitting} size="lg" className="h-12 px-8 rounded-full font-bold">
              {isSubmitting ? 'Create account…' : 'Create account'}
            </Button>
            <Button asChild variant="ghost" className="rounded-full font-bold">
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
