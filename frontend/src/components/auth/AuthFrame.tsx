import type { ReactNode } from 'react'

import { SurfacePanel, SectionEyebrow } from '../ui/foundation'

type AuthFrameProps = {
  eyebrow: string
  title: string
  note: string
  leftTitle: string
  leftSubtitle: string
  leftContent: ReactNode
  rightTitle: string
  rightContent: ReactNode
}

export function AuthFrame({
  eyebrow,
  title,
  note,
  leftTitle,
  leftSubtitle,
  leftContent,
  rightTitle,
  rightContent,
}: AuthFrameProps) {
  return (
    <section className="page-shell py-8 xl:py-10">
      <SurfacePanel className="overflow-hidden rounded-[40px] bg-[#050910] text-white">
        <div className="grid gap-4 border-b border-white/8 px-5 py-5 md:px-8 md:py-6 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-2">
            <SectionEyebrow>{eyebrow}</SectionEyebrow>
            <h1 className="font-display text-3xl font-semibold tracking-[-0.05em] text-white sm:text-4xl">{title}</h1>
          </div>
          <div className="text-sm leading-6 text-white/48 xl:pl-12 xl:text-right">{note}</div>
        </div>

        <div className="grid gap-6 p-5 md:p-8 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-[32px] border border-white/6 bg-white/[0.02] p-6 md:p-8">
            <div className="space-y-4">
              <h2 className="font-display text-4xl font-semibold leading-[0.94] tracking-[-0.07em] text-white sm:text-5xl">
                {leftTitle}
              </h2>
              <p className="max-w-xl text-sm leading-6 text-white/58">{leftSubtitle}</p>
            </div>
            <div className="mt-8">{leftContent}</div>
          </div>

          <div className="rounded-[32px] border border-white/6 bg-white/[0.02] p-6 md:p-8">
            <div className="mb-8 text-xl font-semibold text-white/92">{rightTitle}</div>
            {rightContent}
          </div>
        </div>
      </SurfacePanel>
    </section>
  )
}
