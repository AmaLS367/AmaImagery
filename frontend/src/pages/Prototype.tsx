import { Link } from 'react-router-dom'

import { Button } from '../components/ui/button'
import { appRoutes } from '../lib/routes'

export default function Prototype() {
  return (
    <section className="container space-y-6 py-16">
      <div className="max-w-3xl space-y-3">
        <p className="text-sm uppercase tracking-[0.3em] text-primary">Prototype</p>
        <h1 className="text-4xl font-semibold tracking-tight">Prototype flow has its own page boundary now.</h1>
        <p className="text-muted-foreground">
          This route is in place and ready for the dedicated Figma implementation instead of being folded into another
          screen.
        </p>
      </div>

      <Button asChild variant="outline">
        <Link to={appRoutes.generate}>Back to Generate</Link>
      </Button>
    </section>
  )
}
