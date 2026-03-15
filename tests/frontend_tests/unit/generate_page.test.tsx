import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import Generate from '@src/pages/Generate'

import { mockAnonymousAuth } from './helpers/auth'
import { installFetchMock } from './helpers/fetch'
import { renderWithProviders } from './helpers/render'
import { seedSettings } from './helpers/settings'

describe('Generate page layout coverage', () => {
  it.each(['dashboard', 'editorial', 'cinematic'] as const)('renders every required generation section in %s mode', async (visualMode) => {
    seedSettings({ visualMode })
    installFetchMock([...mockAnonymousAuth()])

    renderWithProviders(<Generate />)

    expect(await screen.findByText('Prompt')).toBeInTheDocument()
    expect(screen.getByText('Negative prompt')).toBeInTheDocument()
    expect(screen.getByText('Dimensions')).toBeInTheDocument()
    expect(screen.getByText('Advanced controls')).toBeInTheDocument()
    expect(screen.getByText('Reference upload')).toBeInTheDocument()
    expect(screen.getByText('Result')).toBeInTheDocument()
  })

  it('does not expose the removed style selector while keeping the hidden style fixed', async () => {
    seedSettings({ visualMode: 'dashboard' })
    installFetchMock([...mockAnonymousAuth()])

    renderWithProviders(<Generate />)

    expect(await screen.findByText('Prompt')).toBeInTheDocument()
    expect(screen.queryByText('Illustration')).not.toBeInTheDocument()
    expect(screen.queryByText('Choose the rendering bias before launch.')).not.toBeInTheDocument()
  })
})
