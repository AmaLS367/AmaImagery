import { Link } from 'react-router-dom'

import { Button } from '../components/ui/button'
import { MetaPill, SectionEyebrow, SurfacePanel } from '../components/ui/foundation'
import { appRoutes } from '../lib/routes'

const runtimePrinciples = [
  {
    title: 'One contract',
    body: 'Status, history, downloads, and errors stay aligned.',
  },
  {
    title: 'One runtime story',
    body: 'Queue behavior and provider health are visible, not implied.',
  },
  {
    title: 'One premium shell',
    body: 'Creator-focused interface with serious controls and clean editorial surfaces.',
  },
]

const landingLinks = [
  { label: 'Log in', href: appRoutes.login },
  { label: 'Create account', href: appRoutes.register },
]

const editorialLinks = [
  { label: 'Prompt Guide', href: appRoutes.promptGuide },
  { label: 'FAQ', href: appRoutes.faq },
  { label: 'About', href: appRoutes.about },
]

export default function Landing() {
  return (
    <section className="page-shell space-y-6 py-8 md:py-10 xl:py-12">
      <div className="space-y-2">
        <SectionEyebrow>Landing</SectionEyebrow>
        <h1 className="font-display text-3xl font-semibold tracking-[-0.05em] sm:text-4xl">HomePage</h1>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.02fr_0.98fr]">
        <div className="relative overflow-hidden rounded-[40px] border border-white/10 bg-[#060a12] p-7 text-white shadow-panel sm:p-9 xl:min-h-[880px]">
          <div className="absolute inset-x-8 bottom-8 h-40 rounded-full bg-[radial-gradient(circle,_rgba(10,132,255,0.18),_transparent_58%)] blur-3xl" />
          <div className="absolute right-20 top-1/2 h-28 w-28 rounded-full bg-[radial-gradient(circle,_rgba(52,211,153,0.22),_transparent_64%)] blur-2xl" />

          <div className="relative flex h-full flex-col gap-10">
            <div className="space-y-6">
              <div className="flex flex-wrap gap-2">
                <MetaPill className="border-white/10 bg-white/5 text-white/70">Product / Creator-Luxury</MetaPill>
                <MetaPill className="border-white/10 bg-white/5 text-white/70">Dark theme</MetaPill>
              </div>

              <div className="space-y-5">
                <h2 className="max-w-[13ch] font-display text-5xl font-semibold leading-[0.92] tracking-[-0.08em] sm:text-6xl">
                  Image generation that feels sharp, calm, and operationally legible.
                </h2>
                <p className="max-w-2xl text-base leading-7 text-white/60">
                  AmaImagery brings together prompt control, queue visibility, history fidelity, and creator-grade
                  output without hiding the actual runtime story.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Button asChild className="bg-[#1bbd9b] text-[#07131b] shadow-[0_24px_60px_-36px_rgba(27,189,155,0.9)] hover:bg-[#26c6a6]">
                  <Link to={appRoutes.generate}>Go to Generate</Link>
                </Button>
                {landingLinks.map((link) => (
                  <Link
                    key={link.href}
                    to={link.href}
                    className="text-sm font-semibold text-white/72 transition-colors hover:text-white"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>

              <div className="flex flex-wrap gap-x-6 gap-y-3 text-sm font-semibold text-white/72">
                {editorialLinks.map((link) => (
                  <Link key={link.href} to={link.href} className="transition-colors hover:text-white">
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>

            <div className="grid gap-5 md:grid-cols-3">
              {runtimePrinciples.map((item) => (
                <div key={item.title} className="space-y-3">
                  <h3 className="font-display text-[1.75rem] font-semibold tracking-[-0.05em] text-white">
                    {item.title}
                  </h3>
                  <p className="text-sm leading-6 text-white/58">{item.body}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <SurfacePanel className="rounded-[40px] bg-[linear-gradient(180deg,_rgba(255,249,239,0.98),_rgba(248,240,224,0.92))] p-7 text-[#151515] shadow-panel sm:p-9 xl:min-h-[880px]">
          <div className="flex h-full flex-col justify-between gap-8">
            <div className="space-y-6">
              <div className="flex flex-wrap gap-2">
                <MetaPill className="border-black/10 bg-black/5 text-black/60">Editorial home</MetaPill>
                <MetaPill className="border-black/10 bg-black/5 text-black/60">Light theme</MetaPill>
              </div>

              <div className="space-y-5">
                <h2 className="max-w-[12ch] font-display text-5xl font-semibold leading-[0.94] tracking-[-0.08em] sm:text-6xl">
                  A trusted screen system for generation, settings, history, and recovery.
                </h2>
                <p className="max-w-2xl text-base leading-7 text-black/52">
                  The light variant keeps the same structure: hero, value, previews, trust blocks, and clean routing
                  into the app and editorial content.
                </p>
              </div>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <SurfacePanel className="rounded-[28px] border-black/5 bg-white/55 p-6 shadow-none">
                <div className="space-y-4">
                  <h3 className="font-display text-2xl font-semibold tracking-[-0.05em]">Feature preview</h3>
                  <p className="text-sm leading-6 text-black/60">
                    Prompt composer with advanced controls, result actions, reference guidance, and stateful
                    generation feedback.
                  </p>
                </div>
              </SurfacePanel>

              <SurfacePanel className="rounded-[28px] border-black/5 bg-white/55 p-6 shadow-none">
                <div className="space-y-4">
                  <h3 className="font-display text-2xl font-semibold tracking-[-0.05em]">Trust &amp; quality</h3>
                  <p className="text-sm leading-6 text-black/60">
                    Explicit queue status, recoverable errors, searchable history, and settings that shape the shell
                    without becoming a token demo.
                  </p>
                </div>
              </SurfacePanel>
            </div>

            <p className="text-sm text-black/45">
              CTA routes: Generate · Login · Register · Guide · FAQ · About
            </p>
          </div>
        </SurfacePanel>
      </div>
    </section>
  )
}
