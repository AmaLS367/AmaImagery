import { useMemo, useState } from 'react'

import { EditorialFrame } from '../components/editorial/EditorialFrame'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { SurfacePanel } from '../components/ui/foundation'

type Category = 'getting-started' | 'quality' | 'runtime' | 'history' | 'account'

type QA = {
  category: Category
  question: string
  answer: string
}

const categories: { id: Category; label: string }[] = [
  { id: 'getting-started', label: 'Getting started' },
  { id: 'quality', label: 'Quality' },
  { id: 'runtime', label: 'Runtime' },
  { id: 'history', label: 'History' },
  { id: 'account', label: 'Account' },
]

const items: QA[] = [
  {
    category: 'getting-started',
    question: 'What should I do before the first run?',
    answer: 'Start with a focused prompt, keep the subject and lighting explicit, and avoid stacking too many stylistic requests at once.',
  },
  {
    category: 'getting-started',
    question: 'When should I use a reference image?',
    answer: 'Add one when pose, framing, or lighting needs to stay anchored. It is usually better than over-describing those constraints in text.',
  },
  {
    category: 'quality',
    question: 'How do I improve output quality?',
    answer: 'Raise steps carefully, keep the scene readable, and use negative guidance for distortion or clutter instead of padding the prompt with unrelated adjectives.',
  },
  {
    category: 'quality',
    question: 'Why do similar prompts still vary?',
    answer: 'The seed, model behavior, and runtime conditions can all shift the result. Save strong outputs to history and reuse their settings when you want consistency.',
  },
  {
    category: 'runtime',
    question: 'What does queued mean?',
    answer: 'Your request has been accepted but is still waiting for an available worker. The generate page keeps that state visible until the provider begins rendering.',
  },
  {
    category: 'runtime',
    question: 'What should I do after an error state?',
    answer: 'Retry with the same settings if the prompt is still valid, or reduce size and CFG if the provider is failing under load.',
  },
  {
    category: 'history',
    question: 'Can I search past generations?',
    answer: 'Yes. History supports prompt search, ratio filters, CFG bands, and a metadata table for scanning steps, seed, and timestamps.',
  },
  {
    category: 'history',
    question: 'How long are results kept?',
    answer: 'The visible archive depth follows your history limit setting, which can be adjusted from the settings control center.',
  },
  {
    category: 'account',
    question: 'Why are login and recovery on different pages?',
    answer: 'The auth flow stays explicit so sign-in, recovery, and reset can each have their own states without collapsing into a single mixed-purpose screen.',
  },
  {
    category: 'account',
    question: 'Where can I change shell behavior?',
    answer: 'Open Settings to control theme, accent, notifications, queue behavior, safety defaults, presets, density, and visual mode.',
  },
]

export default function FAQ() {
  const [query, setQuery] = useState('')
  const [active, setActive] = useState<Category>('getting-started')

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    return items.filter((item) => {
      const matchesCategory = item.category === active
      if (!normalized) return matchesCategory
      return matchesCategory && `${item.question} ${item.answer}`.toLowerCase().includes(normalized)
    })
  }, [query, active])

  return (
    <EditorialFrame
      eyebrow="FAQ"
      title="Production answers for the product, not placeholder support text."
      summary="The FAQ stays concise and searchable, with categories that reflect the actual workflow: getting started, quality, runtime, history, and account handling."
      pills={['Searchable', 'Category-based', 'English-first']}
    >
      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <SurfacePanel className="space-y-4 p-6">
          <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search the FAQ" />
          <div className="grid gap-2">
            {categories.map((category) => (
              <Button
                key={category.id}
                variant={active === category.id ? 'default' : 'secondary'}
                className="justify-start"
                onClick={() => setActive(category.id)}
              >
                {category.label}
              </Button>
            ))}
          </div>
        </SurfacePanel>

        <SurfacePanel className="space-y-4 p-6 md:p-8">
          {filtered.map((item) => (
            <details key={item.question} className="rounded-[24px] border border-border/60 bg-card/60 p-5">
              <summary className="cursor-pointer list-none font-display text-[28px] font-semibold tracking-[-0.05em] text-foreground">
                {item.question}
              </summary>
              <p className="mt-4 text-sm leading-6 text-muted-foreground">{item.answer}</p>
            </details>
          ))}
          {!filtered.length ? (
            <div className="rounded-[24px] border border-border/60 bg-card/60 p-5 text-sm text-muted-foreground">
              No answer matched the current query. Try another keyword or switch categories.
            </div>
          ) : null}
        </SurfacePanel>
      </div>
    </EditorialFrame>
  )
}
