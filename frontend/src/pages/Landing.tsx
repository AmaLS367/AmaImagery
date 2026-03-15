import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ArrowRight, 
  Sparkles, 
  History, 
  Settings as SettingsIcon, 
  ChevronRight, 
  ShieldCheck, 
  Layers, 
  Layout, 
  Zap,
  MousePointer2,
  Cpu,
  Fingerprint,
  Plus,
  Minus
} from 'lucide-react'
import { useState } from 'react'

import { Button } from '../components/ui/button'
import { appRoutes } from '../lib/routes'
import { cn } from '../lib/utils'
import { useSettings } from '../providers/SettingsProvider'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.1 }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] }
  }
}

function GridBackground() {
  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
      <div 
        className="absolute inset-0 opacity-[0.1] dark:opacity-[0.05]" 
        style={{ 
          backgroundImage: `radial-gradient(circle at 2px 2px, currentColor 1px, transparent 0)`,
          backgroundSize: '32px 32px',
          color: 'hsl(var(--primary))'
        }} 
      />
      <div className="absolute inset-0 bg-gradient-to-b from-background via-transparent to-background" />
    </div>
  )
}

function FloatingCard({ children, className, delay = 0 }: { children: React.ReactNode, className?: string, delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30, rotateX: 10 }}
      animate={{ opacity: 1, y: 0, rotateX: 0 }}
      transition={{ delay, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      className={cn("relative z-10", className)}
    >
      <motion.div
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: delay * 0.5 }}
        className="rounded-2xl border border-white/20 bg-white/10 p-5 shadow-2xl backdrop-blur-xl"
      >
        {children}
      </motion.div>
    </motion.div>
  )
}

function FAQItem({ question, answer, isOpen, onClick }: { question: string, answer: string, isOpen: boolean, onClick: () => void }) {
  return (
    <motion.div 
      initial={false}
      className={cn(
        "group overflow-hidden rounded-[32px] border transition-all duration-300",
        isOpen 
          ? "border-primary/40 bg-white shadow-glow dark:bg-white/10" 
          : "border-border bg-secondary/30 hover:border-primary/20 hover:bg-secondary/50 dark:border-white/10 dark:bg-white/5 dark:hover:border-white/20 dark:hover:bg-white/8"
      )}
    >
      <button
        onClick={onClick}
        className="flex w-full items-center justify-between p-8 text-left outline-none"
      >
        <span className={cn(
          "text-lg font-bold transition-colors duration-300",
          isOpen ? "text-primary" : "text-foreground dark:text-white"
        )}>
          {question}
        </span>
        <div className={cn(
          "flex h-8 w-8 items-center justify-center rounded-full border transition-all duration-300",
          isOpen 
            ? "border-primary bg-primary text-primary-foreground rotate-90" 
            : "border-border text-foreground/40 dark:border-white/20 dark:text-white"
        )}>
          {isOpen ? <Minus className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
        </div>
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="px-8 pb-8 pt-0">
              <div className="h-px w-full bg-border mb-6 dark:bg-white/10" />
              <p className="text-base leading-relaxed text-foreground/60 dark:text-white/70">
                {answer}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function Landing() {
  const { t } = useTranslation(['landing', 'common'])
  const { settings } = useSettings()
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  return (
    <div className={cn(
      "relative min-h-screen overflow-hidden bg-background",
      "landing-mode-shell",
      settings.visualMode === 'editorial' && "bg-[radial-gradient(circle_at_top,rgba(249,115,22,0.08),transparent_32%)]",
      settings.visualMode === 'cinematic' && "bg-black text-white",
    )}>
      <GridBackground />

      {/* Hero Section */}
      <section className={cn(
        "page-shell relative z-10 pt-16 pb-20 xl:pt-24 xl:pb-28",
        settings.visualMode === 'editorial' && "pt-20 xl:pt-28",
        settings.visualMode === 'cinematic' && "pt-12 pb-16 xl:pt-20",
      )}>
        <div className="grid gap-12 xl:grid-cols-[1.1fr_450px] xl:items-center">
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="space-y-8"
          >
            <motion.div variants={itemVariants} className="space-y-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                 <Sparkles className="h-3 w-3" />
                 Generation Studio v1.0
              </div>
              <h1 className={cn(
                "font-display text-5xl font-bold leading-[0.95] tracking-tighter text-foreground dark:text-white sm:text-7xl xl:text-[5.8rem]",
                settings.visualMode === 'editorial' && "font-serif font-semibold",
                settings.visualMode === 'cinematic' && "uppercase tracking-[0.02em]",
              )}>
                {t('landing:hero.title').split(' ').map((word, i) => (
                  <span key={i} className={cn(i > 3 ? "text-primary" : "")}>{word} </span>
                ))}
              </h1>
              <p className="max-w-lg text-lg leading-relaxed text-foreground dark:text-white">
                {t('landing:hero.subtitle1')} <span className="text-primary font-bold">{t('landing:hero.subtitle2')}</span>
              </p>
            </motion.div>

            <motion.div variants={itemVariants} className="flex flex-wrap items-center gap-4">
              <Button
                asChild
                size="lg"
                className="h-14 px-10 text-base font-bold bg-primary text-primary-foreground hover:scale-105 transition-all shadow-glow active:scale-95"
              >
                <Link to={appRoutes.generate}>
                  {t('landing:hero.cta_generate')}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-14 px-8 text-base font-bold text-foreground border-border bg-secondary/50 hover:bg-secondary dark:text-white dark:border-white/20 dark:bg-white/5 dark:hover:bg-white/10">
                <Link to={appRoutes.login}>{t('landing:hero.cta_login')}</Link>
              </Button>
            </motion.div>

            <motion.div variants={itemVariants} className="flex items-center gap-6 pt-2">
               <div className="flex -space-x-2.5">
                  {[1,2,3,4].map(i => (
                    <div key={i} className="h-9 w-9 rounded-full border-2 border-background bg-secondary dark:bg-white/10" />
                  ))}
               </div>
               <div className="text-xs font-bold text-foreground uppercase tracking-widest dark:text-white">
                  <span className="text-primary">2,000+</span> creators joined
               </div>
            </motion.div>
          </motion.div>

          <div className="relative hidden xl:block">
             <div className="absolute -inset-20 bg-primary/5 blur-[100px] rounded-full" />
             
             <FloatingCard className="ml-8" delay={0.1}>
                <div className="flex items-center gap-2 mb-4">
                   <div className="h-2 w-2 rounded-full bg-danger/80" />
                   <div className="h-2 w-2 rounded-full bg-warning/80" />
                   <div className="h-2 w-2 rounded-full bg-success/80" />
                </div>
                <div className="space-y-3">
                   <div className="h-2 w-full rounded-full bg-foreground/10 dark:bg-white/20" />
                   <div className="h-2 w-[60%] rounded-full bg-foreground/10 dark:bg-white/20" />
                   <div className="h-10 w-full rounded-xl bg-primary/10 border border-primary/20" />
                </div>
             </FloatingCard>

             <FloatingCard className="-mt-12 -ml-12 w-[300px]" delay={0.25}>
                <div className="flex items-center justify-between mb-6">
                   <div className="text-[9px] font-bold uppercase tracking-[0.25em] text-primary">Runtime Monitor</div>
                   <Zap className="h-3.5 w-3.5 text-primary" />
                </div>
                <div className="space-y-4">
                   <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-foreground dark:text-white">GPU Cluster ALPHA</span>
                      <span className="text-xs font-black text-success uppercase tracking-widest">Stable</span>
                   </div>
                   <div className="h-1.5 w-full rounded-full bg-foreground/10 overflow-hidden dark:bg-white/10">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: '70%' }}
                        transition={{ duration: 2, repeat: Infinity, repeatType: 'reverse' }}
                        className="h-full rounded-full bg-primary" 
                      />
                   </div>
                   <div className="grid grid-cols-2 gap-2">
                      <div className="h-10 rounded-xl bg-secondary border border-border dark:bg-white/5 dark:border-white/10" />
                      <div className="h-10 rounded-xl bg-secondary border border-border dark:bg-white/5 dark:border-white/10" />
                   </div>
                </div>
             </FloatingCard>

             <FloatingCard className="mt-6 ml-16 w-[260px]" delay={0.4}>
                <div className="flex items-center gap-3 mb-4">
                   <div className="h-8 w-8 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                      <MousePointer2 className="h-4 w-4" />
                   </div>
                   <div className="text-xs font-bold uppercase tracking-tight text-foreground dark:text-white">Neural Node</div>
                </div>
                <div className="h-8 w-full rounded-lg bg-primary text-[10px] font-bold flex items-center px-3 text-primary-foreground uppercase tracking-widest">
                   AMA_FUSION_V1
                </div>
             </FloatingCard>
          </div>
        </div>
      </section>

      {/* Capabilities Section */}
      <section className="bg-secondary/30 backdrop-blur-md border-y border-border py-20 relative dark:bg-white/5 dark:border-white/10">
        <div className="page-shell">
          <div className="grid gap-10 md:grid-cols-3">
            {[
              { icon: <Cpu className="h-6 w-6" />, title: t('landing:capabilities.control.title'), body: t('landing:capabilities.control.text') },
              { icon: <Fingerprint className="h-6 w-6" />, title: t('landing:capabilities.history.title'), body: t('landing:capabilities.history.text') },
              { icon: <Layout className="h-6 w-6" />, title: t('landing:capabilities.settings.title'), body: t('landing:capabilities.settings.text') }
            ].map((cap, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="p-8 rounded-[32px] border border-border bg-card shadow-sm space-y-5 dark:border-white/10 dark:bg-white/5 dark:backdrop-blur-xl"
              >
                <div className="h-12 w-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                  {cap.icon}
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold tracking-tight text-foreground dark:text-white">{cap.title}</h3>
                  <p className="text-sm text-foreground/60 leading-relaxed dark:text-white">{cap.body}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Detail */}
      <section className="page-shell py-24 space-y-16">
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold tracking-tighter text-foreground dark:text-white">{t('landing:features.title')}</h2>
          <p className="text-lg text-foreground/70 font-medium dark:text-white">{t('landing:features.subtitle')}</p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {[
            { icon: <Layout className="h-5 w-5" />, title: t('landing:features.workflow.title'), body: t('landing:features.workflow.text') },
            { icon: <Layers className="h-5 w-5" />, title: t('landing:features.history.title'), body: t('landing:features.history.text') },
            { icon: <ShieldCheck className="h-5 w-5" />, title: t('landing:features.predictable.title'), body: t('landing:features.predictable.text') }
          ].map((feature, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -5 }}
              className="p-8 rounded-[32px] border border-border bg-card shadow-xl transition-all hover:bg-secondary/50 hover:border-primary/20 dark:border-white/10 dark:bg-white/10 dark:backdrop-blur-xl dark:shadow-2xl dark:hover:bg-white/15 dark:hover:border-white/30"
            >
              <div className="mb-6 text-primary h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">{feature.icon}</div>
              <h3 className="text-xl font-bold mb-3 text-foreground dark:text-white">{feature.title}</h3>
              <p className="text-foreground/60 leading-relaxed text-sm dark:text-white">{feature.body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* FAQ Section */}
      <section className="page-shell py-24">
        <div className="grid gap-16 xl:grid-cols-[400px_1fr] items-start">
          <div className="space-y-6 sticky top-24">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
              {t('landing:faq.full')}
            </div>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tighter text-foreground leading-[1.1] dark:text-white">
              {t('landing:faq.title')}
            </h2>
            <p className="text-lg text-foreground/60 leading-relaxed font-medium dark:text-white/60">
              {t('landing:faq.subtitle')}
            </p>
          </div>

          <div className="space-y-4">
            {[0, 1, 2].map((i) => (
              <FAQItem 
                key={i}
                question={t(`landing:faq.q${i+1}`)}
                answer={t(`landing:faq.a${i+1}`)}
                isOpen={openFaq === i}
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="relative py-24 overflow-hidden border-t border-border dark:border-white/10">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-primary/5 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
        
        <div className="page-shell relative z-10">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            className="relative overflow-hidden rounded-[48px] border border-border bg-white p-12 md:p-24 shadow-glow text-center dark:border-white/15 dark:bg-white/5 dark:backdrop-blur-2xl dark:shadow-[0_32px_128px_-16px_rgba(0,0,0,0.5)]"
          >
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-1 bg-gradient-to-r from-transparent via-primary to-transparent" />
            
            <div className="space-y-12 max-w-3xl mx-auto">
              <div className="space-y-6">
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.2 }}
                  className="inline-flex items-center gap-2 rounded-full border border-border bg-secondary/50 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-foreground/80 dark:border-white/10 dark:bg-white/5 dark:text-white/80"
                >
                  <Sparkles className="h-3.5 w-3.5 text-primary" />
                  Free Trial Available
                </motion.div>
                
                <h2 className="text-5xl md:text-7xl font-bold tracking-tighter text-foreground dark:text-white">
                  {t('landing:bottom_cta.title')}
                </h2>
                <p className="text-xl text-foreground/70 max-w-xl mx-auto leading-relaxed font-medium dark:text-white/70">
                  {t('landing:bottom_cta.subtitle')}
                </p>
              </div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.4 }}
                className="flex flex-col items-center gap-8"
              >
                <Button 
                  asChild 
                  size="lg" 
                  className="h-16 px-12 text-lg font-bold bg-primary text-primary-foreground hover:scale-105 transition-all shadow-glow group"
                >
                  <Link to={appRoutes.generate}>
                    {t('landing:bottom_cta.button')}
                    <ArrowRight className="ml-2 h-6 w-6 transition-transform group-hover:translate-x-1" />
                  </Link>
                </Button>

                <div className="flex flex-wrap items-center justify-center gap-8">
                  {[
                    { icon: <ShieldCheck className="h-5 w-5" />, label: "Secure" },
                    { icon: <Fingerprint className="h-5 w-5" />, label: "Private" },
                    { icon: <Zap className="h-5 w-5" />, label: "Instant Access" }
                  ].map((item, i) => (
                    <div key={i} className="flex items-center gap-2.5 text-foreground/40 text-xs font-bold uppercase tracking-widest dark:text-white/50">
                      <span className="text-primary">{item.icon}</span>
                      {item.label}
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}
