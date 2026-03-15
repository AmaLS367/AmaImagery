import '@testing-library/jest-dom/vitest'
import '@src/i18n/i18n'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

class IntersectionObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() {
    return []
  }
}

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

Object.defineProperty(globalThis, 'IntersectionObserver', {
  writable: true,
  value: IntersectionObserverMock,
})

Object.defineProperty(globalThis, 'ResizeObserver', {
  writable: true,
  value: ResizeObserverMock,
})

Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: () => {},
})

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
  writable: true,
  value: () => {},
})

class NotificationMock {
  static permission = 'granted'
  static requestPermission = async () => 'granted'

  constructor(_: string, __?: NotificationOptions) {}
}

Object.defineProperty(globalThis, 'Notification', {
  writable: true,
  value: NotificationMock,
})

afterEach(() => {
  cleanup()
  localStorage.clear()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
  document.documentElement.className = ''
  document.documentElement.removeAttribute('data-visual-mode')
  document.documentElement.removeAttribute('data-shell-preset')
  document.documentElement.removeAttribute('data-component-style')
  document.documentElement.removeAttribute('data-density')
  document.documentElement.removeAttribute('data-glass')
  document.documentElement.removeAttribute('data-motion')
})
