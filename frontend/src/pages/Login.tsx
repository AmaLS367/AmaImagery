import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '../components/ui/button'
import '../styles/Register-styles.css'
import { useTranslation } from 'react-i18next'

export default function Login() {
  const { t } = useTranslation()

  type LoginData = { identifier: string; password: string }
  type ForgotData = { identifier: string }
  type FormValues = { identifier: string; password?: string }

  const schemaLogin = z.object({
    identifier: z.string().min(2, t('login:messages.required')),
    password: z.string().min(8, t('register:rules.len')),
  })
  const schemaForgot = z.object({
    identifier: z.string().min(2, t('login:messages.required')),
  })

  const [serverError, setServerError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [mode, setMode] = useState<'login' | 'forgot'>('login')

  const { register, handleSubmit, formState: { errors, isSubmitting }, watch, reset } =
    useForm<FormValues>({ resolver: zodResolver(mode === 'login' ? schemaLogin : schemaForgot), mode: 'onChange' })


  useEffect(() => {
    reset({ identifier: '', ...(mode === 'login' ? { password: '' } : {}) })
    setServerError(null)
    setSuccess(false)
  }, [mode, reset])

  // particles.js — тот же фон
  useEffect(() => {
    const id = 'reg-particles'
    const prefersReduced = typeof window !== 'undefined'
      && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (prefersReduced) return

    let container = document.getElementById(id)
    if (!container) {
      container = document.createElement('div')
      container.id = id
      container.className = 'reg-particles'
      document.body.appendChild(container)
    }

    const init = () => {
      const particlesJS = (window as any).particlesJS
      if (!particlesJS) return
      const BLUE = '#4DA3FF'
      particlesJS(id, {
        particles: {
          number: { value: 90, density: { enable: true, value_area: 900 } },
          color: { value: BLUE }, shape: { type: 'circle' }, opacity: { value: 0.35 },
          size: { value: 3, random: true },
          line_linked: { enable: true, distance: 140, color: BLUE, opacity: 0.25, width: 1 },
          move: { enable: true, speed: 1.0, direction: 'none', straight: false, out_mode: 'out' }
        },
        interactivity: {
          detect_on: 'canvas',
          events: { onhover: { enable: true, mode: 'grab' }, onclick: { enable: true, mode: 'push' }, resize: true },
          modes: { grab: { distance: 160, line_linked: { opacity: 0.35 } }, push: { particles_nb: 3 } }
        },
        retina_detect: true,
      })
    }

    if (!(window as any).particlesJS) {
      const s = document.createElement('script')
      s.src = 'https://cdn.jsdelivr.net/npm/particles.js@2.0.0/particles.min.js'
      s.async = true
      s.onload = init
      document.body.appendChild(s)
    } else init()

    return () => { const n = document.getElementById(id); if (n) n.innerHTML = '' }
  }, [])

  // флоат-лейблы
  useEffect(() => {
    const sub = watch((_all, { name }) => {
      if (!name) return
      const input = document.querySelector<HTMLInputElement>(`#${name}`)
      const field = input?.closest('.reg-field')
      if (input && field) input.value.trim() ? field.classList.add('has-value') : field.classList.remove('has-value')
    })
    setTimeout(() => {
      document.querySelectorAll<HTMLInputElement>('.reg-input').forEach((el) => {
        const field = el.closest('.reg-field')
        if (field) el.value.trim() ? field.classList.add('has-value') : field.classList.remove('has-value')
      })
    }, 0)
    return () => sub.unsubscribe()
  }, [watch])

  const onSubmit = async (data: FormValues) => {
    setServerError(null)
    setSuccess(false)
    try {
      if (mode === 'login') {
        const res = await fetch('/auth/me', {
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
        window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'gen' }))
        setSuccess(true)
      } else {
        const res = await fetch('/auth/forgot-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ identifier: (data as ForgotData).identifier }),
        })
        if (!res.ok && res.status !== 204) throw new Error((await res.text().catch(() => '')) || `Ошибка ${res.status}`)
        setSuccess(true) // «Если такой аккаунт есть — письмо отправлено»
      }
    } catch (e: any) {
      setServerError(e?.message || (mode === 'login' ? 'Ошибка входа' : 'Не удалось отправить письмо'))
    }
  }
  

  return (
    <div className="reg-root">
      <div id="reg-particles" className="reg-particles" aria-hidden="true" />
      <div className="reg-wrap">
        <h1 className="reg-title">
          {mode === 'login' ? t('login:title') : t('reset:modes.request')}
        </h1>

        {success && (
            <div className="reg-alert reg-alert--success">
              {mode === 'login' ? t('login:messages.success') : t('reset:messages.linkSent')}
            </div>
        )}
        {serverError && <div className="reg-alert reg-alert--error">{serverError}</div>}

        <form onSubmit={handleSubmit(onSubmit)} className="reg-form" noValidate>
          <div className="reg-field">
            <input id="identifier" type="text" className="reg-input" autoComplete="username email" {...register('identifier')} />
            <label htmlFor="identifier" className="reg-label">{t('login:fields.emailOrUsername')}</label>
            {errors.identifier && <p className="reg-error">{errors.identifier.message}</p>}
        </div>

        {mode === 'login' && (
          <div className="reg-field">
            <input id="password" type="password" className="reg-input" autoComplete="current-password" {...register('password')} />
            <label htmlFor="password" className="reg-label">{t('login:fields.password')}</label>
            {errors.password && <p className="reg-error">{errors.password.message}</p>}
          </div>
        )}

          <Button type="submit" disabled={isSubmitting} className="reg-submit">
          {isSubmitting
            ? (mode === 'login' ? `${t('login:actions.submit')}…` : `${t('reset:actions.sendLink')}…`)
            : (mode === 'login' ? t('login:actions.submit') : t('reset:actions.sendLink'))}
          </Button>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
            {mode === 'login' ? (
              <button
                type="button"
                onClick={() => setMode('forgot')}
                className="reg-note"
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              >
                {t('login:actions.forgot')}
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setMode('login')}
                className="reg-note"
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              >
                {t('reset:actions.toLogin')}
              </button>
            )}

          </div>
        </form>
      </div>
    </div>
  )
}
