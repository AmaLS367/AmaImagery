import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import Landing from '@src/pages/Landing'

import { mockAnonymousAuth } from './helpers/auth'
import { installFetchMock } from './helpers/fetch'
import { renderWithProviders } from './helpers/render'
import { seedSettings } from './helpers/settings'

describe('Landing page smoke coverage', () => {
  it('renders core ctas and expands the inline faq', async () => {
    seedSettings()
    installFetchMock([...mockAnonymousAuth()])

    renderWithProviders(<Landing />)

    expect(await screen.findByRole('link', { name: /Launch Studio/i })).toHaveAttribute('href', '/generate')
    expect(screen.getByRole('link', { name: /Sign In/i })).toHaveAttribute('href', '/login')

    fireEvent.click(screen.getAllByRole('button').find((button) => button.textContent?.includes('?'))!)
    expect(document.body.textContent).not.toBe('')
  })
})
