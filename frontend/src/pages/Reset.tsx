// src/pages/Reset.tsx
import { useEffect, useMemo, useState } from 'react'
import { Button } from '../components/ui/button'
import '../styles/Register-styles.css'
import { useTranslation } from 'react-i18next'

export default function Reset() {
  const { t } = useTranslation()
  const [pwd1, setPwd1] = useState('')
  const [pwd2, setPwd2] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const token = useMemo(() => {
    try { return new URLSearchParams(window.location.search).get('token') || '' }
    catch { return '' }
  }, [])

  // анимированный фон — тот же particles.js, что и на Login
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

  // флоат-лейблы — как на Login
  useEffect(() => {
    const refresh = () => {
      document.querySelectorAll<HTMLInputElement>('.reg-input').forEach((el) => {
        const field = el.closest('.reg-field')
        if (field) el.value.trim() ? field.classList.add('has-value') : field.classList.remove('has-value')
      })
    }
    setTimeout(refresh, 0)
  }, [])

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (submitting) return
    setError(null)

    if (!token) { setError(t('reset:messages.invalidToken')); return }
    if (pwd1.length < 8) { setError(t('register:rules.len')); return }
    if (pwd1 !== pwd2) { setError(t('reset:messages.mismatch')); return }

    setSubmitting(true)
    try {
      const res = await fetch('/api/v1/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: pwd1 }),
      })
      if (!res.ok) throw new Error(String(res.status))
      setSuccess(true)
      setTimeout(() => {
        try { window.history.replaceState(null, '', '/') } catch {}
        window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'login' }))
      }, 1200)
    } catch (e: any) {
      setError(e?.message || t('reset:messages.invalidToken'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="reg-root">
      <div id="reg-particles" className="reg-particles" aria-hidden="true" />
      <div className="reg-wrap">
        <h1 className="reg-title">{t('reset:title')}</h1>

        {success && <div className="reg-alert reg-alert--success" role="status" aria-live="polite">{t('reset:messages.updated')}</div>}
        {error && <div className="reg-alert reg-alert--error" role="alert" aria-live="assertive">{error}</div>}

        <form className="reg-form" onSubmit={onSubmit} noValidate>
          <div className="reg-field">
            <input
              id="password"
              type="password"
              className="reg-input"
              autoComplete="new-password"
              value={pwd1}
              onChange={(e) => setPwd1(e.target.value)}
              disabled={submitting}
            />
            <label htmlFor="password" className="reg-label">{t('reset:fields.password')}</label>
          </div>

          <div className="reg-field">
            <input
              id="password_confirm"
              type="password"
              className="reg-input"
              autoComplete="new-password"
              value={pwd2}
              onChange={(e) => setPwd2(e.target.value)}
              disabled={submitting}
            />
            <label htmlFor="password_confirm" className="reg-label">{t('reset:fields.confirm')}</label>
          </div>

          <Button type="submit" disabled={submitting || !token} className="reg-submit">
            {submitting ? `${t('reset:actions.apply')}…` : t('reset:actions.apply')}
          </Button>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
            <button
              type="button"
              onClick={() => window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'login' }))}
              className="reg-note"
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
            >
              {t('reset:actions.toLogin')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
