import type { GenerationItem, TaskResp, TaskStatusResp } from '@src/lib/api'
import type { HistoryItem } from '@src/lib/storage'

import { jsonResponse, route, type FetchRoute } from './fetch'

export function makeTaskResp(overrides: Partial<TaskResp> = {}): TaskResp {
  return {
    task_id: 'task-1',
    status: 'queued',
    ...overrides,
  }
}

export function makeTaskStatusResp(overrides: Partial<TaskStatusResp> = {}): TaskStatusResp {
  return {
    task_id: 'task-1',
    status: 'completed',
    image_filename: 'result.png',
    image_url: null,
    exp: 1,
    sig: 'sig',
    ...overrides,
  }
}

export function makeGenerationItem(overrides: Partial<GenerationItem> = {}): GenerationItem {
  return {
    id: 'generation-1',
    image_path: 'result.png',
    image_filename: 'result.png',
    prompt: { prompt: 'Studio portrait' },
    params: { width: 1024, height: 1024, guidance_scale: 7, steps: 28 },
    created_at: new Date('2026-03-01T12:00:00.000Z').toISOString(),
    provider_name: 'AmaFusion',
    ...overrides,
  }
}

export function makeLocalHistoryItem(overrides: Partial<HistoryItem> = {}): HistoryItem {
  return {
    prompt: 'Local portrait',
    neg: '',
    steps: 28,
    guidance: 7,
    width: 1024,
    height: 1024,
    seed: null,
    ipScale: 0.6,
    path: 'local-result.png',
    ts: Date.parse('2026-03-02T12:00:00.000Z'),
    ...overrides,
  }
}

export function mockBackendHistory(items: GenerationItem[]): FetchRoute[] {
  return [
    route('/api/v1/users/me/generations', () => jsonResponse({ total: items.length, items })),
  ]
}

export function mockGenerationLifecycle(states: TaskStatusResp[]): FetchRoute[] {
  let index = 0
  return [
    route('/api/v1/images/generate', () => jsonResponse(makeTaskResp()), 'POST'),
    route('/api/v1/images/status/', () => {
      const state = states[Math.min(index, states.length - 1)] ?? makeTaskStatusResp()
      index += 1
      return jsonResponse(state)
    }),
  ]
}
