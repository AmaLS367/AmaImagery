import { Link } from 'react-router-dom'

import { Button } from '../components/ui/button'
import { appRoutes } from '../lib/routes'

export default function Landing() {
  return (
    <section className="container flex min-h-[calc(100vh-8rem)] flex-col justify-center gap-8 py-16">
      <div className="max-w-3xl space-y-4">
        <p className="text-sm uppercase tracking-[0.3em] text-primary">AmaImagery</p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Create visuals with a dedicated landing page instead of dropping users straight into the workspace.
        </h1>
        <p className="max-w-2xl text-base text-muted-foreground sm:text-lg">
          This route now exists as its own screen. The production layout and copy from Figma will replace this
          scaffold in the next commits.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button asChild size="lg">
          <Link to={appRoutes.generate}>Open Generator</Link>
        </Button>
        <Button asChild size="lg" variant="outline">
          <Link to={appRoutes.about}>Learn More</Link>
        </Button>
      </div>
    </section>
  )
}
