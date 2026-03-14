import { Link } from 'react-router-dom'

import { Button } from '../components/ui/button'
import { MetaPill, SectionEyebrow, SurfacePanel } from '../components/ui/foundation'
import { appRoutes } from '../lib/routes'

const startPoints = [
  { label: 'Landing', href: appRoutes.landing },
  { label: 'Login', href: appRoutes.login },
  { label: 'Register', href: appRoutes.register },
  { label: 'Generate', href: appRoutes.generate },
  { label: 'FAQ', href: appRoutes.faq },
  { label: '404', href: appRoutes.notFound },
] as const

const flowSections = [
  {
    title: 'Primary route chain',
    description: 'Landing -> Generate -> Queued -> Running -> Completed -> History -> Settings',
    steps: ['Landing', 'Generate', 'Queued', 'Running', 'Completed', 'History', 'Settings'],
  },
  {
    title: 'Auth chain',
    description: 'Landing -> Login -> Forgot Password -> Reset Password -> Login -> Generate',
    steps: ['Landing', 'Login', 'Forgot Password', 'Reset Password', 'Login', 'Generate'],
  },
  {
    title: 'Editorial and recovery',
    description:
      'Landing footer -> About -> FAQ -> Prompt Guide -> Privacy | 404 -> Landing -> FAQ -> Prompt Guide',
    steps: ['Landing footer', 'About', 'FAQ', 'Prompt Guide', 'Privacy', '404', 'Landing'],
  },
] as const

const verificationNotes = [
  'This screen documents the prototype routes and major CTA flows for handoff and verification.',
  'Full clickthrough map and start states for the Figma file.',
] as const

export default function Prototype() {
  return (
    <section className="page-shell space-y-6 py-8 xl:py-10">
      <SurfacePanel glass className="space-y-6 p-6 md:p-8">
        <div className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr] xl:items-end">
          <div className="space-y-4">
            <SectionEyebrow>Prototype</SectionEyebrow>
            <h1 className="font-display text-4xl font-semibold tracking-[-0.07em] text-foreground sm:text-5xl">
              Full clickthrough map and start states for the Figma file.
            </h1>
            <p className="max-w-3xl text-base leading-7 text-muted-foreground">
              This route preserves the prototype map as its own screen instead of burying it inside another page. It
              is the handoff view for verifying route boundaries, CTA paths, and recovery loops.
            </p>
          </div>

          <div className="grid gap-3">
            {verificationNotes.map((note) => (
              <div key={note} className="rounded-[24px] border border-border/60 bg-card/60 px-5 py-4 text-sm leading-6 text-muted-foreground">
                {note}
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link to={appRoutes.landing}>Open Landing</Link>
          </Button>
          <Button asChild variant="secondary">
            <Link to={appRoutes.generate}>Open Generate</Link>
          </Button>
        </div>
      </SurfacePanel>

      <div className="grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
        <SurfacePanel className="space-y-4 p-6">
          <div className="text-sm font-semibold text-foreground">Start points</div>
          <div className="grid gap-3">
            {startPoints.map((point) => (
              <Link
                key={point.href}
                to={point.href}
                className="flex min-h-[60px] items-center justify-between rounded-[22px] border border-border/60 bg-card/70 px-4 text-sm font-semibold text-foreground transition-colors hover:bg-card"
              >
                <span>{point.label}</span>
                <span className="text-muted-foreground">Route</span>
              </Link>
            ))}
          </div>
        </SurfacePanel>

        <div className="grid gap-6">
          {flowSections.map((section) => (
            <SurfacePanel key={section.title} className="space-y-5 p-6 md:p-7">
              <div className="space-y-2">
                <h2 className="font-display text-3xl font-semibold tracking-[-0.06em] text-foreground">
                  {section.title}
                </h2>
                <p className="text-sm leading-6 text-muted-foreground">{section.description}</p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {section.steps.map((step, index) => (
                  <div key={`${section.title}-${step}-${index}`} className="flex items-center gap-2">
                    <MetaPill>{step}</MetaPill>
                    {index < section.steps.length - 1 ? <span className="text-sm font-semibold text-muted-foreground">-&gt;</span> : null}
                  </div>
                ))}
              </div>
            </SurfacePanel>
          ))}
        </div>
      </div>
    </section>
  )
}
