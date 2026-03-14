import type { ReactNode } from 'react'

import { MetaPill, SectionEyebrow, SurfacePanel } from '../ui/foundation'

type EditorialFrameProps = {
  eyebrow: string
  title: string
  summary: string
  pills?: string[]
  children: ReactNode
}

export function EditorialFrame({ eyebrow, title, summary, pills = [], children }: EditorialFrameProps) {
  return (
    <section className="page-shell space-y-6 py-8 xl:py-10">
      <SurfacePanel glass className="space-y-5 p-6 md:p-8">
        <SectionEyebrow>{eyebrow}</SectionEyebrow>
        <div className="space-y-4">
          <h1 className="font-display text-4xl font-semibold tracking-[-0.06em] text-foreground sm:text-5xl">
            {title}
          </h1>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">{summary}</p>
        </div>
        {pills.length ? (
          <div className="flex flex-wrap gap-2">
            {pills.map((pill) => (
              <MetaPill key={pill}>{pill}</MetaPill>
            ))}
          </div>
        ) : null}
      </SurfacePanel>
      {children}
    </section>
  )
}
