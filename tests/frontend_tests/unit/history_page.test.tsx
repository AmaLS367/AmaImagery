import { fireEvent, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import History from '@src/pages/History'

import { mockAnonymousAuth, mockAuthenticatedAuth } from './helpers/auth'
import { installFetchMock } from './helpers/fetch'
import { makeGenerationItem, mockBackendHistory } from './helpers/history'
import { renderWithProviders } from './helpers/render'
import { seedAnonymousHistory, seedSettings } from './helpers/settings'

describe('History page sources and filters', () => {
  it('loads backend history for authenticated users', async () => {
    seedSettings()
    installFetchMock([
      ...mockAuthenticatedAuth(),
      ...mockBackendHistory([
        makeGenerationItem({ id: 'g1', prompt: { prompt: 'Backend portrait' } }),
      ]),
    ])

    renderWithProviders(<History />)

    expect((await screen.findAllByText('Backend portrait')).length).toBeGreaterThan(0)
  })

  it('loads local history for anonymous users', async () => {
    seedSettings()
    seedAnonymousHistory(2)
    installFetchMock([...mockAnonymousAuth()])

    renderWithProviders(<History />)

    expect((await screen.findAllByText('Local prompt 1')).length).toBeGreaterThan(0)
  })

  it('shows the empty state when backend history is empty', async () => {
    seedSettings()
    installFetchMock([
      ...mockAuthenticatedAuth(),
      ...mockBackendHistory([]),
    ])

    renderWithProviders(<History />)

    expect(await screen.findByText('No generations yet')).toBeInTheDocument()
  })

  it('filters by search text and ratio', async () => {
    seedSettings()
    installFetchMock([
      ...mockAuthenticatedAuth(),
      ...mockBackendHistory([
        makeGenerationItem({ id: 'a', prompt: { prompt: 'Portrait alpha' }, params: { width: 1024, height: 1024, guidance_scale: 7, steps: 28 } }),
        makeGenerationItem({ id: 'b', prompt: { prompt: 'Landscape beta' }, params: { width: 1024, height: 576, guidance_scale: 9, steps: 30 } }),
      ]),
    ])

    renderWithProviders(<History />)

    expect((await screen.findAllByText('Portrait alpha')).length).toBeGreaterThan(0)
    fireEvent.change(screen.getByPlaceholderText('Search generations...'), { target: { value: 'landscape' } })

    await waitFor(() => expect(screen.queryAllByText('Portrait alpha')).toHaveLength(0))
    expect(screen.getAllByText('Landscape beta').length).toBeGreaterThan(0)

    fireEvent.change(screen.getAllByRole('combobox')[0]!, { target: { value: '1:1' } })
    await waitFor(() => expect(screen.getByText('No results found')).toBeInTheDocument())
  })
})
