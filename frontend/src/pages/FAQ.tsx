import { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, ChevronRight, Plus, Minus } from 'lucide-react'

import { EditorialFrame } from '../components/editorial/EditorialFrame'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { SurfacePanel } from '../components/ui/foundation'
import { cn } from '../lib/utils'

type Category = 'getting-started' | 'quality' | 'runtime' | 'history' | 'account'

const categories: { id: Category; label: string }[] = [
  { id: 'getting-started', label: 'Getting started' },
  { id: 'quality', label: 'Quality' },
  { id: 'runtime', label: 'Runtime' },
  { id: 'history', label: 'History' },
  { id: 'account', label: 'Account' },
]

const items: { category: Category; question: string; answer: string }[] = [
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

function FAQItem({ question, answer, isOpen, onClick }: { question: string, answer: string, isOpen: boolean, onClick: () => void }) {
  return (
    <div className={cn(
      "overflow-hidden rounded-3xl border transition-all duration-300",
      isOpen ? "border-primary/40 bg-white shadow-glow dark:bg-white/10" : "border-border bg-card/50 hover:border-primary/20 dark:border-white/5"
    )}>
      <button
        onClick={onClick}
        className="flex w-full items-center justify-between p-6 text-left"
      >
        <span className={cn(
          "text-xl font-bold tracking-tight transition-colors",
          isOpen ? "text-primary" : "text-foreground dark:text-white"
        )}>
          {question}
        </span>
        <div className={cn(
          "flex h-8 w-8 items-center justify-center rounded-full border transition-all duration-300",
          isOpen ? "border-primary bg-primary text-primary-foreground rotate-90" : "border-border text-foreground/40 dark:border-white/20 dark:text-white"
        )}>
          {isOpen ? <Minus className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
        </div>
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="px-6 pb-6 pt-0">
              <div className="h-px w-full bg-border mb-4 dark:bg-white/10" />
              <p className="text-base leading-relaxed text-foreground/60 dark:text-white/70 font-medium">
                {answer}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function FAQ() {
  const [query, setQuery] = useState('')
  const [active, setActive] = useState<Category>('getting-started')
  const [openQuestion, setOpenQuestion] = useState<string | null>(null)

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
      title="Production answers for the product, not placeholder text."
      summary="The FAQ stays concise and searchable, with categories that reflect the actual workflow: getting started, quality, runtime, history, and account handling."
      pills={['Searchable', 'Category-based', 'English-first']}
    >
      <div className="grid gap-12 xl:grid-cols-[320px_1fr] items-start">
        <SurfacePanel className="p-6 space-y-8 sticky top-24">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground/40" />
            <Input 
              value={query} 
              onChange={(e) => setQuery(e.target.value)} 
              placeholder="Search the FAQ" 
              className="pl-10 h-12 rounded-full border-border bg-secondary/50"
            />
          </div>
          
          <div className="space-y-1">
            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-primary px-3 mb-4">Categories</h4>
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => {
                  setActive(category.id)
                  setOpenQuestion(null)
                }}
                className={cn(
                  "flex w-full items-center justify-between rounded-full px-4 py-3 text-sm font-bold transition-all",
                  active === category.id 
                    ? "bg-primary text-primary-foreground shadow-glow" 
                    : "text-foreground/60 hover:bg-black/5 dark:text-white/60 dark:hover:bg-white/5"
                )}
              >
                {category.label}
                {active === category.id && <ChevronRight className="h-4 w-4" />}
              </button>
            ))}
          </div>
        </SurfacePanel>

        <div className="space-y-4 min-h-[400px]">
          <AnimatePresence mode="popLayout">
            {filtered.map((item) => (
              <motion.div
                key={item.question}
                layout
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <FAQItem 
                  question={item.question}
                  answer={item.answer}
                  isOpen={openQuestion === item.question}
                  onClick={() => setOpenQuestion(openQuestion === item.question ? null : item.question)}
                />
              </motion.div>
            ))}
          </AnimatePresence>
          
          {!filtered.length && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-20 text-center space-y-4"
            >
              <div className="h-16 w-16 rounded-full bg-secondary flex items-center justify-center dark:bg-white/5">
                <Search className="h-8 w-8 text-foreground/20" />
              </div>
              <div className="space-y-1">
                <p className="font-bold text-foreground dark:text-white">No results found</p>
                <p className="text-sm text-foreground/40 dark:text-white/40">Try adjusting your search query or category.</p>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </EditorialFrame>
  )
}
