import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { GeneratePayload, TaskResp, TaskStatusResp } from '@src/lib/api'
import { generateJSON, getTaskStatus } from '@src/lib/api'
import { getHistory } from '@src/lib/storage'
import { JobProvider, useJobs } from '@src/providers/JobProvider'
import { useOptionalAuth } from '@src/providers/AuthProvider'
import { SettingsProvider } from '@src/providers/SettingsProvider'

import { makeTaskResp, makeTaskStatusResp } from './helpers/history'
import { seedSettings } from './helpers/settings'

vi.mock('@src/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@src/lib/api')>('@src/lib/api')
  return {
    ...actual,
    generateJSON: vi.fn(),
    getTaskStatus: vi.fn(),
  }
})

vi.mock('@src/providers/AuthProvider', () => ({
  useOptionalAuth: vi.fn(),
}))

const mockedGenerateJSON = vi.mocked(generateJSON)
const mockedGetTaskStatus = vi.mocked(getTaskStatus)
const mockedUseOptionalAuth = vi.mocked(useOptionalAuth)

const payload: GeneratePayload = {
  prompt: 'Studio portrait',
  negative_prompt: 'blur',
  steps: 28,
  guidance_scale: 7,
  width: 1024,
  height: 1024,
  seed: null,
  ip_scale: 0.6,
  style: 'realistic',
}

function JobHarness() {
  const { jobs, start, cancel } = useJobs()

  return (
    <div>
      <button onClick={() => start(payload)}>start</button>
      <button onClick={() => jobs[0] && cancel(jobs[0].id)}>cancel</button>
      <div data-testid="summary">
        {jobs.map((job) => `${job.status}:${job.backendStatus ?? 'none'}`).join('|') || 'empty'}
      </div>
    </div>
  )
}

function renderHarness() {
  return render(
    <SettingsProvider>
      <JobProvider>
        <JobHarness />
      </JobProvider>
    </SettingsProvider>,
  )
}

async function flush() {
  await Promise.resolve()
  await Promise.resolve()
}

async function advancePoll() {
  await vi.advanceTimersByTimeAsync(2000)
  await flush()
}

describe('JobProvider', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    seedSettings()
    mockedUseOptionalAuth.mockReturnValue({ status: 'anonymous' } as any)
    mockedGenerateJSON.mockReset()
    mockedGetTaskStatus.mockReset()
    mockedGenerateJSON.mockResolvedValue(makeTaskResp())
  })

  it('creates a queued job and completes it for anonymous history', async () => {
    mockedGetTaskStatus
      .mockResolvedValueOnce(makeTaskStatusResp({ status: 'running', image_filename: null }) as TaskStatusResp)
      .mockResolvedValue(makeTaskStatusResp({ status: 'completed', image_filename: 'anon.png' }) as TaskStatusResp)

    renderHarness()
    fireEvent.click(screen.getByText('start'))
    await flush()
    expect(screen.getByTestId('summary').textContent).toMatch(/queued:queued|running:running/)

    await advancePoll()
    await advancePoll()

    expect(screen.getByTestId('summary')).toHaveTextContent('completed:completed')
    expect(getHistory()).toHaveLength(1)
  })

  it('does not write local history for authenticated users', async () => {
    mockedUseOptionalAuth.mockReturnValue({ status: 'authenticated' } as any)
    mockedGetTaskStatus.mockResolvedValue(makeTaskStatusResp({ status: 'completed', image_filename: 'auth.png' }) as TaskStatusResp)

    renderHarness()
    fireEvent.click(screen.getByText('start'))
    await flush()
    await advancePoll()

    expect(screen.getByTestId('summary')).toHaveTextContent('completed:completed')
    expect(getHistory()).toEqual([])
  })

  it('maps failed backend status to ui error while preserving backendStatus', async () => {
    mockedGetTaskStatus.mockResolvedValue(makeTaskStatusResp({ status: 'failed', error: 'provider failed', image_filename: null }) as TaskStatusResp)

    renderHarness()
    fireEvent.click(screen.getByText('start'))
    await flush()
    await advancePoll()

    expect(screen.getByTestId('summary')).toHaveTextContent('error:failed')
  })

  it('cancels the active job on user request', async () => {
    mockedGetTaskStatus.mockResolvedValue(makeTaskStatusResp({ status: 'running', image_filename: null }) as TaskStatusResp)

    renderHarness()
    fireEvent.click(screen.getByText('start'))
    await flush()
    fireEvent.click(screen.getByText('cancel'))
    await advancePoll()

    expect(screen.getByTestId('summary')).toHaveTextContent('canceled:canceled')
  })
})
