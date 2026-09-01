import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { GeneratePayload } from '@src/lib/api'
import Generate from '@src/pages/Generate'
import { useJobs } from '@src/providers/JobProvider'
import { SettingsProvider } from '@src/providers/SettingsProvider'

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

describe('Generate submission behavior', () => {
  beforeEach(() => {
    Object.defineProperty(URL, 'createObjectURL', {
      writable: true,
      value: vi.fn(() => 'blob:preview'),
    })
    Object.defineProperty(URL, 'revokeObjectURL', {
      writable: true,
      value: vi.fn(),
    })
    mockedUseJobs.mockReturnValue({
      jobs: [],
      start: vi.fn(() => 'job-1'),
      cancel: vi.fn(),
      get: vi.fn(() => undefined),
      anyRunning: false,
    })
  })

  it('validates prompt length before submission', async () => {
    seedSettings()
    renderGenerate()

    fireEvent.change(screen.getByPlaceholderText('Fashion portrait in editorial midnight studio, precise eyes, quiet confidence, polished chrome accents.'), {
      target: { value: 'ab' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))

    expect(await screen.findByText('Prompt needs at least three characters.')).toBeInTheDocument()
  })

  it('sends a backend-valid payload with realistic style and appended banlist', async () => {
    seedSettings({ banlist: 'nsfw, gore' })
    const start = vi.fn<(payload: GeneratePayload) => string>(() => 'job-1')
    mockedUseJobs.mockReturnValue({
      jobs: [],
      start,
      cancel: vi.fn(),
      get: vi.fn(() => undefined),
      anyRunning: false,
    })

    renderGenerate()

    fireEvent.change(screen.getByPlaceholderText('Fashion portrait in editorial midnight studio, precise eyes, quiet confidence, polished chrome accents.'), {
      target: { value: 'Runtime-safe portrait prompt' },
    })
    fireEvent.change(screen.getByPlaceholderText('blurry, extra digits, distorted face, low contrast, noisy skin'), {
      target: { value: 'blur, low detail' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))

    await waitFor(() => expect(start).toHaveBeenCalledTimes(1))
    const firstCall = start.mock.calls[0]
    const payload = firstCall?.[0]
    if (!payload) {
      throw new Error('Expected generation payload')
    }
    expect(payload).toMatchObject({
      prompt: 'Runtime-safe portrait prompt',
      negative_prompt: 'blur, low detail, nsfw, gore',
      style: 'realistic',
    })
    expect(payload.steps).toBeTypeOf('number')
    expect(payload.guidance_scale).toBeTypeOf('number')
    expect(payload.width).toBeTypeOf('number')
    expect(payload.height).toBeTypeOf('number')
    expect(payload.ip_scale).toBeTypeOf('number')
  })

  it('rejects non-image reference uploads and oversized files', async () => {
    seedSettings()
    const { container } = renderGenerate()

    const input = container.querySelector('input[type="file"]') as HTMLInputElement | null
    expect(input).not.toBeNull()

    fireEvent.change(input!, { target: { files: [new File(['text'], 'note.txt', { type: 'text/plain' })] } })
    expect(await screen.findByText('Reference upload accepts image files only.')).toBeInTheDocument()

    const largeFile = new File([new Uint8Array(8 * 1024 * 1024 + 1)], 'large.png', { type: 'image/png' })
    fireEvent.change(input!, { target: { files: [largeFile] } })
    expect(await screen.findByText('Reference upload is limited to 8 MB.')).toBeInTheDocument()
  })
})
