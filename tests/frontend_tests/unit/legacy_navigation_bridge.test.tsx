import { render, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { describe, expect, it } from 'vitest'

import { LegacyNavigationBridge } from '@src/components/LegacyNavigationBridge'

describe('LegacyNavigationBridge', () => {
  it('redirects legacy tab events to canonical routes', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <LegacyNavigationBridge />
        <Routes>
          <Route path="/" element={<div>home</div>} />
          <Route path="/settings" element={<div>settings-target</div>} />
        </Routes>
      </MemoryRouter>,
    )

    window.dispatchEvent(new CustomEvent('goto-tab', { detail: 'settings' }))

    await waitFor(() => expect(document.body).toHaveTextContent('settings-target'))
  })
})
