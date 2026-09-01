import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { GenerationErrorState } from '@src/components/GenerationErrorState'

describe('GenerationErrorState component', () => {
  it('renders general error title, advice for allocation failure, and buttons', () => {
    const onRetry = vi.fn()
    const onDismiss = vi.fn()

    render(
      <GenerationErrorState
        error="ComfyUI ModelMMAP allocation failed: out of memory"
        tone="dashboard"
        onRetry={onRetry}
        onDismiss={onDismiss}
      />
    )

    expect(screen.getByText('Generation Failed')).toBeInTheDocument()
    expect(
      screen.getByText(/GPU memory allocation failure. Try reducing image dimensions or steps./i),
    ).toBeInTheDocument()

    const retryBtn = screen.getByRole('button', { name: /Retry/i })
    expect(retryBtn).toBeInTheDocument()
    fireEvent.click(retryBtn)
    expect(onRetry).toHaveBeenCalledTimes(1)

    const dismissBtn = screen.getByRole('button', { name: /Dismiss/i })
    expect(dismissBtn).toBeInTheDocument()
    fireEvent.click(dismissBtn)
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('toggles technical details visibility and copies log', async () => {
    const errorText = 'ComfyUI exception: ModelMMAP allocation failed at comfy/model_management.py'
    
    // Mock navigator.clipboard
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    })

    render(
      <GenerationErrorState
        error={errorText}
        tone="cinematic"
      />
    )

    // Details should be closed by default
    expect(screen.queryByText(errorText)).not.toBeInTheDocument()

    const toggleBtn = screen.getByRole('button', { name: /Show technical details/i })
    fireEvent.click(toggleBtn)

    // Now technical details should be open
    expect(screen.getByText(errorText)).toBeInTheDocument()

    const copyBtn = screen.getByRole('button', { name: /Copy/i })
    fireEvent.click(copyBtn)
    expect(writeTextMock).toHaveBeenCalledWith(errorText)
  })
})
