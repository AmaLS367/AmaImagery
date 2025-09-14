import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '../components/ui/button'
import '../styles/Register-styles.css'
import { useTranslation } from 'react-i18next'

export default function Register() {
  const { t } = useTranslation()

  type FormData = {
    email: string
    username: string
    password: string
    confirm: string
    agree?: boolean
  }

  const schema = z.object({
    email: z.string().min(1, t('register:messages.required')).email(t('register:messages.invalidEmail')),
    username: z.string().min(2, t('register:messages.required')),
    password: z.string().min(8, t('register:rules.len')),
    confirm: z.string().min(8, t('register:rules.len')),
    agree: z.boolean().optional()
  }).refine((v) => v.password === v.confirm, {
    message: t('register:messages.mismatch'),
    path: ['confirm']
  })

  const [serverError, setServerError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    watch,
  } = useForm<FormData>({ resolver: zodResolver(schema), mode: 'onChange' })

  // particles.js CDN + инициализация (синий фон)
  useEffect(() => {
    const id = 'reg-particles'
    const prefersReduced =
      typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
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
          color: { value: BLUE },
          shape: { type: 'circle' },
          opacity: { value: 0.35 },
          size: { value: 3, random: true },
          line_linked: {
            enable: true,
            distance: 140,
            color: BLUE,
            opacity: 0.25,
            width: 1,
          },
          move: {
            enable: true,
            speed: 1.0,
            direction: 'none',
            random: false,
            straight: false,
            out_mode: 'out',
            bounce: false,
            attract: { enable: false, rotateX: 600, rotateY: 1200 },
          },
        },
        interactivity: {
          detect_on: 'canvas',
          events: {
            onhover: { enable: true, mode: 'grab' },
            onclick: { enable: true, mode: 'push' },
            resize: true,
          },
          modes: {
            grab: { distance: 160, line_linked: { opacity: 0.35 } },
            push: { particles_nb: 3 },
            repulse: { distance: 140, duration: 0.3 },
          },
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
    } else {
      init()
    }

    return () => {
      const node = document.getElementById(id)
      if (node) node.innerHTML = ''
    }
  }, [])

  // Флоат-лейблы без плейсхолдеров: переключаем .has-value на .reg-field
  useEffect(() => {
    const sub = watch((_all, { name }) => {
      if (!name) return
      const input = document.querySelector<HTMLInputElement>(`#${name}`)
      const field = input?.closest('.reg-field')
      if (input && field) {
        input.value.trim() ? field.classList.add('has-value') : field.classList.remove('has-value')
      }
    })
    // Инициализация на первый рендер
    setTimeout(() => {
      document.querySelectorAll<HTMLInputElement>('.reg-input').forEach((el) => {
        const field = el.closest('.reg-field')
        if (field) el.value.trim() ? field.classList.add('has-value') : field.classList.remove('has-value')
      })
    }, 0)
    return () => sub.unsubscribe()
  }, [watch])

  const handleInput = (e: React.FormEvent<HTMLInputElement>) => {
    const el = e.currentTarget
    const field = el.closest('.reg-field')
    if (field) el.value.trim() ? field.classList.add('has-value') : field.classList.remove('has-value')
  }

  const onSubmit = async (data: FormData) => {
    setServerError(null)
    setSuccess(false)
    try {
      const res = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: data.email, password: data.password, username: data.username }),
      })
      if (!res.ok) {
        const text = await res.text().catch(() => '')
        throw new Error(text || `Ошибка ${res.status}`)
      }
      const payload = await res.json().catch(() => null)
  
      // Помечаем пользователя как вошедшего, чтобы топбар переключился
      try { localStorage.setItem('auth', JSON.stringify({ loggedIn: true, user: payload })) } catch {}
      window.dispatchEvent(new CustomEvent('auth:update'))
  
      // Редирект на генерацию
      window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'gen' }))
  
      setSuccess(true)
      reset({ username: '', email: '', password: '', confirm: '' })
    } catch (e: any) {
      setServerError(e?.message || 'Ошибка запроса')
    }
  }  

  return (
    <div className="reg-root">
      <div id="reg-particles" className="reg-particles" aria-hidden="true" />

      <div className="reg-wrap">
        <h1 className="reg-title">{t('register:title')}</h1>

        {success && <div className="reg-alert reg-alert--success">{t('register:messages.success')}</div>}
        {serverError && <div className="reg-alert reg-alert--error">{serverError}</div>}

        <form onSubmit={handleSubmit(onSubmit)} className="reg-form" noValidate>
          <div className="reg-field">
            <input id="username" type="text" className="reg-input" autoComplete="username" {...register('username')} onInput={handleInput}/>
            <label htmlFor="username" className="reg-label">{t('register:fields.username')}</label>
            {errors.username && <p className="reg-error">{errors.username.message}</p>}
          </div>

          <div className="reg-field">
            <input id="email" type="email" className="reg-input" autoComplete="email" {...register('email')} onInput={handleInput}/>
            <label htmlFor="email" className="reg-label">{t('register:fields.email')}</label>
            {errors.email && <p className="reg-error">{errors.email.message}</p>}
          </div>

          <div className="reg-field">
            <input id="password" type="password" className="reg-input" autoComplete="new-password" {...register('password')} onInput={handleInput}/>
            <label htmlFor="password" className="reg-label">{t('register:fields.password')}</label>
            {errors.password && <p className="reg-error">{errors.password.message}</p>}
          </div>

          <div className="reg-field">
            <input id="confirm" type="password" className="reg-input" autoComplete="new-password" {...register('confirm')} onInput={handleInput}/>
            <label htmlFor="confirm" className="reg-label">{t('register:fields.confirm')}</label>
            {errors.confirm && <p className="reg-error">{errors.confirm.message}</p>}
          </div>

          <Button type="submit" disabled={isSubmitting} className="reg-submit">
            {isSubmitting ? `${t('register:actions.submit')}…` : t('register:actions.submit')}
          </Button>

          <p className="reg-note">{t('register:note')}</p>
        </form>
      </div>
    </div>
  )
}
