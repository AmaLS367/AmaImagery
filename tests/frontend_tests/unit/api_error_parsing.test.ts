import { describe, expect, it } from 'vitest'

import { parseApiError } from '@src/lib/api'

describe('parseApiError', () => {
  it('returns plain text bodies as-is', async () => {
    const response = new Response('plain failure', {
      status: 400,
      headers: { 'Content-Type': 'text/plain' },
    })

    await expect(parseApiError(response)).resolves.toBe('plain failure')
  })

  it('reads json detail fields', async () => {
    const response = new Response(JSON.stringify({ detail: 'bad request' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    })

    await expect(parseApiError(response)).resolves.toBe('bad request')
  })

  it('formats validation details arrays', async () => {
    const response = new Response(JSON.stringify({
      detail: [
        { loc: ['body', 'prompt'], msg: 'too short' },
        { loc: ['body', 'width'], msg: 'invalid width' },
      ],
    }), {
      status: 422,
      headers: { 'Content-Type': 'application/json' },
    })

    await expect(parseApiError(response)).resolves.toBe('body.prompt: too short; body.width: invalid width')
  })

  it('reads nested error details arrays', async () => {
    const response = new Response(JSON.stringify({
      error: {
        details: [
          { loc: ['settings', 'theme'], msg: 'unsupported theme' },
        ],
      },
    }), {
      status: 422,
      headers: { 'Content-Type': 'application/json' },
    })

    await expect(parseApiError(response)).resolves.toBe('settings.theme: unsupported theme')
  })
})
