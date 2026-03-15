import { describe, expect, it, vi } from 'vitest'

import { RequestQueue } from '@src/lib/queue'

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

describe('RequestQueue policy handling', () => {
  it('respects max parallelism', async () => {
    const queue = new RequestQueue(2, false)
    const first = deferred<void>()
    const second = deferred<void>()
    const third = deferred<void>()
    const started: string[] = []

    queue.run(async () => {
      started.push('first')
      await first.promise
    })
    queue.run(async () => {
      started.push('second')
      await second.promise
    })
    queue.run(async () => {
      started.push('third')
      await third.promise
    })

    expect(started).toEqual(['first', 'second'])

    first.resolve()
    await Promise.resolve()
    await Promise.resolve()
    expect(started).toEqual(['first', 'second', 'third'])

    second.resolve()
    third.resolve()
  })

  it('cancels older queued work when cancelPrevious is enabled', async () => {
    const queue = new RequestQueue(1, true)
    const first = deferred<void>()
    const started = vi.fn()

    const active = queue.run(async () => {
      started('active')
      await first.promise
    })
    const queued = queue.run(async () => {
      started('queued')
    })
    const replacement = queue.run(async () => {
      started('replacement')
    })

    await expect(queued.promise).rejects.toMatchObject({ name: 'AbortError' })

    first.resolve()
    await active.promise
    await replacement.promise

    expect(started.mock.calls.map(([label]) => label)).toEqual(['active', 'replacement'])
  })

  it('preserves order for queued tasks', async () => {
    const queue = new RequestQueue(1, false)
    const calls: string[] = []

    await Promise.all([
      queue.run(async () => { calls.push('first') }).promise,
      queue.run(async () => { calls.push('second') }).promise,
      queue.run(async () => { calls.push('third') }).promise,
    ])

    expect(calls).toEqual(['first', 'second', 'third'])
  })

  it('does not leak aborted queued tasks into execution', async () => {
    const queue = new RequestQueue(1, false)
    const blocker = deferred<void>()
    const started = vi.fn()

    const active = queue.run(async () => {
      started('active')
      await blocker.promise
    })
    const queued = queue.run(async (signal) => {
      if (signal.aborted) throw new DOMException('Aborted', 'AbortError')
      started('queued')
    })

    queued.abort()
    blocker.resolve()
    await active.promise

    await expect(queued.promise).rejects.toMatchObject({ name: 'AbortError' })
    expect(started.mock.calls.map(([label]) => label)).toEqual(['active'])
  })
})
