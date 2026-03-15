import { loadSettings, type Settings } from '@src/lib/settings'
import { addHistory } from '@src/lib/storage'

import { makeLocalHistoryItem } from './history'

export function seedSettings(overrides: Partial<Settings> = {}) {
  const base = loadSettings()
  const next = {
    ...base,
    ...overrides,
    queue: {
      ...base.queue,
      ...(overrides.queue ?? {}),
    },
  }
  localStorage.setItem('amaimagery.settings.v3', JSON.stringify(next))
  return next
}

export function seedAnonymousHistory(count = 1) {
  localStorage.removeItem('amaimagery.history.v2')
  for (let index = 0; index < count; index += 1) {
    addHistory(
      makeLocalHistoryItem({
        path: `local-${index}.png`,
        prompt: `Local prompt ${index}`,
        ts: Date.parse(`2026-03-${String(index + 1).padStart(2, '0')}T12:00:00.000Z`),
      }),
    )
  }
}
