import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import Generate from '@src/pages/Generate'
import { useJobs } from '@src/providers/JobProvider'
import { SettingsProvider } from '@src/providers/SettingsProvider'

import { makeTaskStatusResp } from './helpers/history'
import { seedSettings } from './helpers/settings'

vi.mock('@src/providers/JobProvider', () => ({
  useJobs: vi.fn(),
}))

const mockedUseJobs = vi.mocked(useJobs)

function renderGenerate() {
  return render(
    <MemoryRouter>
      <SettingsProvider>
        <Generate />
      </SettingsProvider>
    </MemoryRouter>,
  )
}

describe('Generate runtime states', () => {
  it('shows the queue state when an active queued job exists', async () => {
    seedSettings()
    localStorage.setItem('amaimagery.activeJobId', 'job-1')
    const queuedJob = {
      id: 'job-1',
      status: 'queued' as const,
      backendStatus: 'queued' as const,
      payload: {
        prompt: 'Queued prompt',
        negative_prompt: null,
        steps: 28,
        guidance_scale: 7,
        width: 1024,
        height: 1024,
        seed: null,
        ip_scale: 0.6,
        style: 'realistic' as const,
      },
      startedAt: Date.now(),
    }

    mockedUseJobs.mockReturnValue({
      jobs: [queuedJob],
      start: vi.fn(),
      cancel: vi.fn(),
      get: vi.fn(() => queuedJob),
      anyRunning: true,
    })

    renderGenerate()

    expect(await screen.findByText(/Queue position/)).toBeInTheDocument()
  })

  it('shows completed state with history and download actions', async () => {
    seedSettings()
    localStorage.setItem('amaimagery.activeJobId', 'job-1')
    const completedJob = {
      id: 'job-1',
      status: 'completed' as const,
      backendStatus: 'completed' as const,
      payload: {
        prompt: 'Completed prompt',
        negative_prompt: null,
        steps: 28,
        guidance_scale: 7,
        width: 1024,
        height: 1024,
        seed: null,
        ip_scale: 0.6,
        style: 'realistic' as const,
      },
      result: makeTaskStatusResp({ status: 'completed', image_filename: 'result.png' }),
      startedAt: Date.now(),
      finishedAt: Date.now(),
    }

    mockedUseJobs.mockReturnValue({
      jobs: [completedJob],
      start: vi.fn(),
      cancel: vi.fn(),
      get: vi.fn(() => completedJob),
      anyRunning: false,
    })

    renderGenerate()

    await waitFor(() => expect(screen.getByText('Generation completed')).toBeInTheDocument())
    expect(screen.getAllByRole('link', { name: 'View history' }).length).toBeGreaterThan(0)
    expect(screen.getByRole('link', { name: 'Download image' })).toBeInTheDocument()
  })

  it('shows retry controls when the active job failed', async () => {
    seedSettings()
    localStorage.setItem('amaimagery.activeJobId', 'job-1')
    const failedJob = {
      id: 'job-1',
      status: 'error' as const,
      backendStatus: 'failed' as const,
      payload: {
        prompt: 'Failed prompt',
        negative_prompt: null,
        steps: 28,
        guidance_scale: 7,
        width: 1024,
        height: 1024,
        seed: null,
        ip_scale: 0.6,
        style: 'realistic' as const,
      },
      error: 'provider crash',
      startedAt: Date.now(),
      finishedAt: Date.now(),
    }

    mockedUseJobs.mockReturnValue({
      jobs: [failedJob],
      start: vi.fn(() => 'job-2'),
      cancel: vi.fn(),
      get: vi.fn(() => failedJob),
      anyRunning: false,
    })

    renderGenerate()

    await waitFor(() => expect(screen.getByRole('button', { name: 'Retry with same settings' })).toBeInTheDocument())
  })
})
