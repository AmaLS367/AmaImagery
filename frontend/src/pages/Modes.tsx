import { Link } from 'react-router-dom'

import { Button } from '../components/ui/button'
import { MetaPill, SectionEyebrow, SurfacePanel } from '../components/ui/foundation'
import { appRoutes } from '../lib/routes'

const directionCards = [
  {
    title: 'Main Product',
    subtitle: 'Creator-Luxury',
    body:
      'Linear + Arc inspired. High-contrast shell, premium glow, disciplined metadata, and dark-first operational confidence.',
    labels: ['Generate', 'History', 'Settings'],
    previewClass:
      'bg-[radial-gradient(circle_at_top_left,rgba(6,182,212,0.24),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(45,212,191,0.18),transparent_34%),linear-gradient(180deg,#07111b,#060b12)] text-white',
  },
  {
    title: 'Editorial',
    subtitle: 'Reading surfaces',
    body: 'Airy reading surfaces, sharp section rhythm, generous margins, and trustworthy document styling.',
    labels: ['About', 'FAQ', 'Prompt Guide'],
    previewClass:
      'bg-[linear-gradient(180deg,rgba(255,249,239,0.98),rgba(248,240,224,0.92))] text-[#181818]',
  },
  {
    title: 'Glass / Cinematic',
    subtitle: 'Atmospheric focus',
    body: 'Blurred volume, atmospheric depth, and polished card translucency for focused creator moments.',
    labels: ['Visual Lab', 'Glow', 'Overlay'],
    previewClass:
      'bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.32),transparent_32%),radial-gradient(circle_at_top_right,rgba(168,85,247,0.28),transparent_30%),linear-gradient(180deg,#08121f,#0a1321)] text-white',
  },
  {
    title: 'Dashboard',
    subtitle: 'Dense operations',
    body:
      'Dense information handling for history, metrics, and operational monitoring without becoming clinical.',
    labels: ['Filters', 'Tables', 'Metrics'],
    previewClass:
      'bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.2),transparent_28%),linear-gradient(180deg,#eef7f5,#e4f0eb)] text-[#13231d]',
  },
] as const

const activationNotes = [
  'Curated visual direction study, not full product duplication.',
  'Only the main product shell and settings visual lab expose alternate modes.',
] as const

export default function Modes() {
  return (
    <section className="page-shell space-y-6 py-8 xl:py-10">
      <SurfacePanel className="overflow-hidden rounded-[40px] bg-[#060a12] p-6 text-white md:p-8 xl:p-10">
        <div className="grid gap-8 xl:grid-cols-[1.02fr_0.98fr] xl:items-end">
          <div className="space-y-5">
            <SectionEyebrow className="border-white/12 bg-white/[0.04] text-white/72">Modes</SectionEyebrow>
            <div className="space-y-4">
              <h1 className="font-display text-4xl font-semibold tracking-[-0.07em] text-white sm:text-5xl xl:text-6xl">
                Curated visual direction study for the AmaImagery shell.
              </h1>
              <p className="max-w-3xl text-base leading-7 text-white/60">
                This route keeps the visual references separate from the functional pages. It documents the approved
                directions and clarifies where those modes actually surface in production.
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {activationNotes.map((note) => (
              <div key={note} className="rounded-[28px] border border-white/10 bg-white/[0.04] p-5 text-sm leading-6 text-white/68">
                {note}
              </div>
            ))}
          </div>
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild className="bg-[#1bbd9b] text-[#061017] hover:bg-[#26c6a6]">
            <Link to={appRoutes.settings}>Open Settings</Link>
          </Button>
          <Button asChild variant="secondary" className="border-white/10 bg-white/[0.06] text-white hover:bg-white/[0.1]">
            <Link to={appRoutes.generate}>Open Generate</Link>
          </Button>
        </div>
      </SurfacePanel>

      <div className="grid gap-5 xl:grid-cols-2">
        {directionCards.map((card) => (
          <SurfacePanel key={card.title} className="overflow-hidden rounded-[32px] p-0">
            <div className={`border-b border-black/5 px-6 py-6 md:px-7 ${card.previewClass}`}>
              <div className="flex flex-wrap items-center gap-2">
                <MetaPill className="border-current/15 bg-current/10 text-current/80">{card.title}</MetaPill>
                <MetaPill className="border-current/15 bg-current/10 text-current/80">{card.subtitle}</MetaPill>
              </div>
              <div className="mt-5 grid gap-4 md:grid-cols-[1fr_160px] md:items-end">
                <div className="space-y-3">
                  <h2 className="font-display text-3xl font-semibold tracking-[-0.06em]">{card.title}</h2>
                  <p className="max-w-2xl text-sm leading-6 text-current/72">{card.body}</p>
                </div>
                <div className="rounded-[24px] border border-current/10 bg-current/5 p-4">
                  <div className="h-24 rounded-[18px] border border-current/10 bg-current/5" />
                </div>
              </div>
            </div>

            <div className="space-y-5 p-6 md:p-7">
              <div className="flex flex-wrap gap-2">
                {card.labels.map((label) => (
                  <MetaPill key={label}>{label}</MetaPill>
                ))}
              </div>

              <div className="text-sm leading-6 text-muted-foreground">
                {card.title === 'Main Product'
                  ? 'This is the live production shell used by Generate, History, and Settings.'
                  : card.title === 'Editorial'
                    ? 'This direction shapes the public-reading pages and reference content.'
                    : card.title === 'Glass / Cinematic'
                      ? 'This direction is exposed through the settings visual lab and shell adjustments.'
                      : 'This direction informs dense information handling across history and admin surfaces.'}
              </div>
            </div>
          </SurfacePanel>
        ))}
      </div>
    </section>
  )
}
