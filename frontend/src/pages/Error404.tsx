import { Link } from 'react-router'
import { motion } from 'framer-motion'
import { ArrowLeft, Home, Sparkles, Compass } from 'lucide-react'

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
    <section className="page-shell py-12 xl:py-24 space-y-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <SurfacePanel className="p-12 md:p-20 text-center space-y-10 relative overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-1/2 bg-primary/5 blur-[120px] rounded-full pointer-events-none" />
          
          <div className="space-y-6 relative z-10">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-xs font-black uppercase tracking-[0.3em] text-primary mx-auto">
              <Sparkles className="h-3.5 w-3.5" />
              Error 404
            </div>
            
            <div className="space-y-4 max-w-4xl mx-auto">
              <h1 className="font-display text-5xl md:text-8xl font-bold tracking-tight text-foreground dark:text-white leading-[0.9]">
                This route is not part of the screen system.
              </h1>
              <p className="max-w-2xl mx-auto text-lg md:text-xl text-foreground/60 dark:text-white/60 font-medium leading-relaxed">
                AmaImagery keeps page boundaries explicit. The URL you opened does not resolve to a valid product, auth, editorial, or visual-lab route.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap justify-center gap-4 relative z-10">
            <Button asChild size="lg" className="h-14 px-10 rounded-full font-bold shadow-glow">
              <Link to={appRoutes.landing}>
                <Home className="mr-2 h-5 w-5" />
                Return Home
              </Link>
            </Button>
            <Button variant="outline" size="lg" className="h-14 px-10 rounded-full font-bold border-border" onClick={() => history.back()}>
              <ArrowLeft className="mr-2 h-5 w-5" />
              Go Back
            </Button>
          </div>
        </SurfacePanel>
      </motion.div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {quickLinks.map((link, i) => (
          <motion.div
            key={link.href}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * (i + 1) }}
          >
            <SurfacePanel className="h-full p-8 space-y-6 flex flex-col hover:border-primary/30 transition-colors">
              <div className="space-y-3 flex-1">
                <div className="h-10 w-10 rounded-2xl bg-secondary flex items-center justify-center dark:bg-white/5">
                   <Compass className="h-5 w-5 text-primary" />
                </div>
                <h2 className="font-display text-2xl font-bold tracking-tight text-foreground dark:text-white">{link.title}</h2>
                <p className="text-sm text-foreground/60 dark:text-white/60 font-medium leading-relaxed">{link.description}</p>
              </div>
              <Button asChild variant="ghost" className="w-full justify-between rounded-full font-bold hover:bg-primary/5 hover:text-primary group">
                <Link to={link.href} className="flex items-center justify-between w-full">
                  Open Route
                  <Sparkles className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              </Button>
            </SurfacePanel>
          </motion.div>
        ))}
      </div>
    </section>
  )
}
