import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import { AuthFrame } from '@src/components/auth/AuthFrame'
import { SettingsProvider } from '@src/providers/SettingsProvider'

describe('AuthFrame', () => {
  it('renders header and both content slots', () => {
    render(
      <MemoryRouter>
        <SettingsProvider>
          <AuthFrame
            eyebrow="Login"
            title="Frame title"
            note="Frame note"
            leftTitle="Left title"
            leftSubtitle="Left subtitle"
            leftContent={<div>left-slot</div>}
            rightTitle="Right title"
            rightContent={<div>right-slot</div>}
          />
        </SettingsProvider>
      </MemoryRouter>,
    )

    expect(screen.getByText('Frame title')).toBeInTheDocument()
    expect(screen.getByText('left-slot')).toBeInTheDocument()
    expect(screen.getByText('right-slot')).toBeInTheDocument()
  })
})
