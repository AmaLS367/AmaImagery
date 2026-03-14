import { Link } from 'react-router-dom'

import { Button } from '../components/ui/button'
import { appRoutes } from '../lib/routes'

export default function Modes() {
  return (
    <section className="container space-y-6 py-16">
      <div className="max-w-3xl space-y-3">
        <p className="text-sm uppercase tracking-[0.3em] text-primary">Modes</p>
        <h1 className="text-4xl font-semibold tracking-tight">Visual modes live on a dedicated route now.</h1>
        <p className="text-muted-foreground">
          This placeholder keeps the screen separate while the production implementation from Figma is built in the
          later UI commits.
        </p>
      </div>

      <Button asChild>
        <Link to={appRoutes.settings}>Open Settings</Link>
      </Button>
    </section>
  )
}
