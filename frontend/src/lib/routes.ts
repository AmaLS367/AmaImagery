export const appRoutes = {
  landing: '/',
  generate: '/generate',
  history: '/history',
  settings: '/settings',
  login: '/login',
  register: '/register',
  forgotPassword: '/forgot-password',
  resetPassword: '/reset-password',
  about: '/about',
  faq: '/faq',
  promptGuide: '/prompt-guide',
  privacy: '/privacy',

  notFound: '/404',
} as const

export type LegacyTab =
  | 'gen'
  | 'history'
  | 'settings'
  | 'guide'
  | 'about'
  | 'faq'
  | 'privacy'
  | 'register'
  | 'login'
  | 'reset'
  | 'error404'

export const legacyTabRoutes: Record<LegacyTab, string> = {
  gen: appRoutes.generate,
  history: appRoutes.history,
  settings: appRoutes.settings,
  guide: appRoutes.promptGuide,
  about: appRoutes.about,
  faq: appRoutes.faq,
  privacy: appRoutes.privacy,
  register: appRoutes.register,
  login: appRoutes.login,
  reset: appRoutes.resetPassword,
  error404: appRoutes.notFound,
}

export function resolveLegacyTabRoute(tab: string | null | undefined) {
  if (!tab) return null
  return legacyTabRoutes[tab as LegacyTab] ?? null
}
