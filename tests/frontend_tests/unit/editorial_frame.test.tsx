import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { EditorialFrame } from '@src/components/editorial/EditorialFrame'
import { SettingsProvider } from '@src/providers/SettingsProvider'

describe('EditorialFrame', () => {
  it('renders hero copy and pills', () => {
    render(
      <SettingsProvider>
        <EditorialFrame eyebrow="Guide" title="Editorial title" summary="Editorial summary" pills={['One', 'Two']}>
          <div>frame-body</div>
        </EditorialFrame>
      </SettingsProvider>,
    )

    expect(screen.getByText('Editorial title')).toBeInTheDocument()
    expect(screen.getByText('Editorial summary')).toBeInTheDocument()
    expect(screen.getByText('One')).toBeInTheDocument()
    expect(screen.getByText('frame-body')).toBeInTheDocument()
  })
})
