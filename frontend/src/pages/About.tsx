import { Link } from 'react-router-dom'

import { EditorialFrame } from '../components/editorial/EditorialFrame'
import { Button } from '../components/ui/button'
import { SectionHeading, SurfacePanel } from '../components/ui/foundation'
import { appRoutes } from '../lib/routes'

const principles = [
  {
    title: 'One product contract',
    body: 'Generation, history, settings, and recovery share the same runtime story instead of feeling like stitched demos.',
  },
  {
    title: 'Operational clarity',
    body: 'Queue visibility, retries, saved metadata, and explicit states make the tool readable when real runs are happening.',
  },
  {
    title: 'Premium shell',
    body: 'Editorial surfaces and serious controls coexist so the product feels creator-grade without hiding the mechanics.',
  },
]

const workflow = [
  {
    title: 'Compose with intent',
    body: 'Write a focused prompt, add reference guidance when needed, and keep negative constraints explicit.',
  },
  {
    title: 'Read the runtime',
    body: 'Queue status, provider progress, and recoverable errors stay visible while the generation is active.',
  },
  {
    title: 'Reuse what works',
    body: 'Saved history, metadata filters, and shell presets make it easier to repeat strong results without losing context.',
  },
]

export default function About() {
  return (
    <EditorialFrame
      eyebrow="About"
      title="AmaImagery is a premium image-generation shell built around clarity."
      summary="The product keeps generation, history, settings, and recovery as separate real pages while preserving one coherent runtime story for the user."
      pills={['Creator-focused', 'Readable runtime', 'Editorial shell']}
    >
      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <SurfacePanel className="space-y-6 p-6 md:p-8">
          <SectionHeading
            title="Why the system exists"
            description="The interface is designed so prompt work, queue behavior, history fidelity, and shell controls all feel like parts of the same product instead of separate experiments."
          />
          <div className="grid gap-4">
            {principles.map((principle) => (
              <SurfacePanel key={principle.title} className="rounded-[24px] p-5 shadow-none">
                <h2 className="font-display text-[28px] font-semibold tracking-[-0.05em]">{principle.title}</h2>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">{principle.body}</p>
              </SurfacePanel>
            ))}
          </div>
        </SurfacePanel>

        <SurfacePanel className="space-y-6 p-6 md:p-8">
          <SectionHeading
            title="How the flow works"
            description="Each major screen owns a different job, but the product contract stays consistent from first prompt to saved result."
          />
          <ol className="space-y-4">
            {workflow.map((step, index) => (
              <li key={step.title} className="flex gap-4 rounded-[24px] border border-border/60 bg-card/60 p-5">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/12 font-semibold text-primary">
                  {index + 1}
                </div>
                <div>
                  <div className="font-display text-2xl font-semibold tracking-[-0.05em] text-foreground">{step.title}</div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{step.body}</p>
                </div>
              </li>
            ))}
          </ol>
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link to={appRoutes.promptGuide}>Open Prompt Guide</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to={appRoutes.history}>View History</Link>
            </Button>
            <Button asChild variant="ghost">
              <Link to={appRoutes.settings}>Control the shell</Link>
            </Button>
          </div>
        </SurfacePanel>
      </div>
    </EditorialFrame>
  )
}
