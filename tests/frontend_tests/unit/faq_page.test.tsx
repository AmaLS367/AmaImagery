import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import FAQ from '@src/pages/FAQ'

import { mockAnonymousAuth } from './helpers/auth'
import { installFetchMock } from './helpers/fetch'
import { renderWithProviders } from './helpers/render'
import { seedSettings } from './helpers/settings'

describe('FAQ page smoke coverage', () => {
  it('filters faq entries by category and search', async () => {
    seedSettings()
    installFetchMock([...mockAnonymousAuth()])

    renderWithProviders(<FAQ />)

    expect(await screen.findByText('Production answers for the product, not placeholder text.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Runtime' }))
    fireEvent.change(screen.getByPlaceholderText('Search the FAQ'), { target: { value: 'queued' } })

    expect(await screen.findByText('What does queued mean?')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'What does queued mean?' }))
    expect(screen.getByText(/accepted but is still waiting for an available worker/i)).toBeInTheDocument()
  })
})
