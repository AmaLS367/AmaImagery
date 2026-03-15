import { render, type RenderOptions } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { AuthProvider } from '@src/providers/AuthProvider'
import { JobProvider } from '@src/providers/JobProvider'
import { SettingsProvider } from '@src/providers/SettingsProvider'

type WrapperOptions = {
  route?: string
}

export function renderWithProviders(ui: React.ReactElement, options: WrapperOptions & Omit<RenderOptions, 'wrapper'> = {}) {
  const { route = '/', ...renderOptions } = options
  window.history.pushState({}, '', route)

  return render(ui, {
    wrapper: ({ children }) => (
      <MemoryRouter initialEntries={[route]}>
        <SettingsProvider>
          <AuthProvider>
            <JobProvider>{children}</JobProvider>
          </AuthProvider>
        </SettingsProvider>
      </MemoryRouter>
    ),
    ...renderOptions,
  })
}

export function renderRoute(route: string, ui: React.ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return renderWithProviders(ui, { route, ...options })
}
