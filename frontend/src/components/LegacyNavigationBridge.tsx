import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import { resolveLegacyTabRoute } from '../lib/routes'

export function LegacyNavigationBridge() {
  const navigate = useNavigate()

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<string>).detail
      const nextRoute = resolveLegacyTabRoute(detail)
      if (nextRoute) {
        navigate(nextRoute)
      }
    }

    window.addEventListener('goto-tab', handler)
    return () => window.removeEventListener('goto-tab', handler)
  }, [navigate])

  return null
}
