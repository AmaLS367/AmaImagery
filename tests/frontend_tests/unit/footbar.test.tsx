import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import { Footbar } from '@src/components/Footbar'
import { SettingsProvider } from '@src/providers/SettingsProvider'

describe('Footbar', () => {
  it('renders canonical internal and support links', () => {
    render(
      <MemoryRouter>
        <SettingsProvider>
          <Footbar />
        </SettingsProvider>
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: 'About' })).toHaveAttribute('href', '/about')
    expect(screen.getByRole('link', { name: 'Privacy' })).toHaveAttribute('href', '/privacy')
    expect(screen.getByRole('link', { name: 'Prompt guide' })).toHaveAttribute('href', '/prompt-guide')
    expect(screen.getByRole('link', { name: 'Support' })).toHaveAttribute('href', 'mailto:support@amaimagery.com')
  })
})
