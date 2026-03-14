import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

import { EditorialFrame } from '../components/editorial/EditorialFrame'
import { Button } from '../components/ui/button'
import { SectionHeading, SurfacePanel } from '../components/ui/foundation'
import { appRoutes } from '../lib/routes'

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

const item = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0 }
}

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
      eyebrow="About AmaImagery"
      title="A premium image-generation shell built around absolute clarity."
      summary="The product keeps generation, history, settings, and recovery as separate real pages while preserving one coherent runtime story for the user."
      pills={['Creator-focused', 'Readable runtime', 'Editorial shell']}
    >
      <div className="grid gap-12 xl:grid-cols-[1fr_1fr] items-start">
        <motion.div 
          variants={container}
          initial="hidden"
          animate="show"
          className="space-y-10"
        >
          <SectionHeading
            title="Why the system exists"
            description="The interface is designed so prompt work, queue behavior, history fidelity, and shell controls all feel like parts of the same product instead of separate experiments."
          />
          <div className="grid gap-6">
            {principles.map((principle) => (
              <motion.div key={principle.title} variants={item}>
                <SurfacePanel className="p-8 space-y-4 hover:border-primary/30 transition-colors">
                  <h3 className="font-display text-2xl font-bold tracking-tight text-foreground dark:text-white">
                    {principle.title}
                  </h3>
                  <p className="text-base text-foreground/60 dark:text-white/60 leading-relaxed">
                    {principle.body}
                  </p>
                </SurfacePanel>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div 
          variants={container}
          initial="hidden"
          animate="show"
          className="space-y-10"
        >
          <SectionHeading
            title="How the flow works"
            description="Each major screen owns a different job, but the product contract stays consistent from first prompt to saved result."
          />
          <ol className="space-y-4">
            {workflow.map((step, index) => (
              <motion.li key={step.title} variants={item}>
                <SurfacePanel className="flex gap-6 p-8 group hover:border-primary/30 transition-colors">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10 font-bold text-primary group-hover:scale-110 transition-transform">
                    {index + 1}
                  </div>
                  <div className="space-y-2">
                    <div className="font-display text-2xl font-bold tracking-tight text-foreground dark:text-white">
                      {step.title}
                    </div>
                    <p className="text-base text-foreground/60 dark:text-white/60 leading-relaxed">
                      {step.body}
                    </p>
                  </div>
                </SurfacePanel>
              </motion.li>
            ))}
          </ol>
          <div className="flex flex-wrap gap-4 pt-4">
            <Button asChild size="lg" className="h-14 px-8 rounded-full font-bold">
              <Link to={appRoutes.promptGuide}>Open Prompt Guide</Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="h-14 px-8 rounded-full font-bold border-border">
              <Link to={appRoutes.history}>View History</Link>
            </Button>
          </div>
        </motion.div>
      </div>
    </EditorialFrame>
  )
}
