import { describe, expect, it } from 'vitest'

import { addHistory, getHistory, loadForm, saveForm } from '@src/lib/storage'

describe('storage helpers', () => {
  it('saves and loads the generation form', () => {
    saveForm({
      prompt: 'Portrait prompt',
      neg: 'blur',
      steps: 28,
      guidance: 7,
      width: 1024,
      height: 1024,
      seed: 11,
      ipScale: 0.6,
      style: 'realistic',
    })

    expect(loadForm()).toEqual({
      prompt: 'Portrait prompt',
      neg: 'blur',
      steps: 28,
      guidance: 7,
      width: 1024,
      height: 1024,
      seed: 11,
      ipScale: 0.6,
      style: 'realistic',
    })
  })

  it('returns null when the saved form is malformed', () => {
    localStorage.setItem('amaimagery.form.v1', '{bad')
    expect(loadForm()).toBeNull()
  })

  it('deduplicates history by path', () => {
    addHistory({
      prompt: 'One',
      neg: '',
      steps: 24,
      guidance: 6,
      width: 1024,
      height: 1024,
      seed: null,
      ipScale: 0.6,
      path: 'same.png',
      ts: 1,
    })
    addHistory({
      prompt: 'Two',
      neg: '',
      steps: 28,
      guidance: 7,
      width: 896,
      height: 1024,
      seed: null,
      ipScale: 0.6,
      path: 'same.png',
      ts: 2,
    })

    const history = getHistory()
    expect(history).toHaveLength(1)
    expect(history[0]?.prompt).toBe('Two')
  })

  it('caps local history to 500 entries', () => {
    for (let index = 0; index < 520; index += 1) {
      addHistory({
        prompt: `Prompt ${index}`,
        neg: '',
        steps: 24,
        guidance: 6,
        width: 1024,
        height: 1024,
        seed: null,
        ipScale: 0.6,
        path: `${index}.png`,
        ts: index,
      })
    }

    const history = getHistory()
    expect(history).toHaveLength(500)
    expect(history[0]?.path).toBe('519.png')
    expect(history.at(-1)?.path).toBe('20.png')
  })

  it('returns an empty list when persisted history is malformed', () => {
    localStorage.setItem('amaimagery.history.v2', '{broken')
    expect(getHistory()).toEqual([])
  })
})
