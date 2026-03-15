import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import PromptGuide from '@src/pages/PromptGuide'

import { mockAnonymousAuth } from './helpers/auth'
import { installFetchMock } from './helpers/fetch'
import { renderWithProviders } from './helpers/render'
import { seedSettings } from './helpers/settings'

describe('PromptGuide page smoke coverage', () => {
  it('renders the main prompt guidance sections', async () => {
    seedSettings()
    installFetchMock([...mockAnonymousAuth()])

    renderWithProviders(<PromptGuide />)

    expect(await screen.findByText('Master the art of explicit guidance.')).toBeInTheDocument()
    expect(screen.getByText('Quick Rules')).toBeInTheDocument()
    expect(screen.getByText('Recommended')).toBeInTheDocument()
    expect(screen.getByText('To Avoid')).toBeInTheDocument()
    expect(screen.getByText('Correction Habit')).toBeInTheDocument()
  })
})
