import { Link } from 'react-router-dom'

import { Button } from '../components/ui/button'
import { SurfacePanel } from '../components/ui/foundation'
import { appRoutes } from '../lib/routes'

const quickLinks = [
  {
    title: 'Generate',
    description: 'Return to the main workspace for prompt composition and runtime feedback.',
    href: appRoutes.generate,
  },
  {
    title: 'History',
    description: 'Inspect saved generations, metadata filters, and runtime records.',
    href: appRoutes.history,
  },
  {
    title: 'Prompt Guide',
    description: 'Review the editorial guidance for prompt structure and correction habits.',
    href: appRoutes.promptGuide,
  },
  {
    title: 'FAQ',
    description: 'Open the product-facing answers for runtime, history, and account questions.',
    href: appRoutes.faq,
  },
] as const

export default function Error404() {
  return (
    <section className="page-shell space-y-6 py-12 xl:py-16">
      <SurfacePanel className="space-y-6 overflow-hidden rounded-[40px] bg-[#050910] p-8 text-white md:p-10">
        <div className="inline-flex rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-semibold tracking-[0.2em] text-white/68">
          404
        </div>
        <div className="space-y-4">
          <h1 className="font-display text-6xl font-semibold tracking-[-0.08em] text-white md:text-8xl">This route is not part of the screen system.</h1>
          <p className="max-w-3xl text-base leading-7 text-white/58">
            AmaImagery keeps page boundaries explicit. The URL you opened does not resolve to a valid product, auth, editorial, or visual-lab route.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link to={appRoutes.landing}>Go to homepage</Link>
          </Button>
          <Button asChild variant="secondary">
            <Link to={appRoutes.generate}>Open Generate</Link>
          </Button>
          <Button variant="ghost" onClick={() => history.back()}>
            Go back
          </Button>
        </div>
      </SurfacePanel>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {quickLinks.map((link) => (
          <SurfacePanel key={link.href} className="space-y-4 p-5">
            <h2 className="font-display text-2xl font-semibold tracking-[-0.05em] text-foreground">{link.title}</h2>
            <p className="text-sm leading-6 text-muted-foreground">{link.description}</p>
            <Button asChild variant="ghost">
              <Link to={link.href}>Open route</Link>
            </Button>
          </SurfacePanel>
        ))}
      </div>
    </section>
  )
}
