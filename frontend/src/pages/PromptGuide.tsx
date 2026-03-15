import { motion } from 'framer-motion'
import { CheckCircle2, XCircle, Lightbulb, Terminal, Layers } from 'lucide-react'

import { EditorialFrame } from '../components/editorial/EditorialFrame'
import { SurfacePanel, SectionHeading } from '../components/ui/foundation'
import { cn } from '../lib/utils'

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

const templates = [
  {
    title: 'Prompt formula',
    code: 'Subject + scene + composition + lighting + finish + constraints',
    detail: 'Keep the prompt legible. A short, explicit structure usually performs better than a paragraph of loosely related descriptors.',
  },
  {
    title: 'Portrait starter',
    code: 'Editorial portrait, confident subject, waist-up crop, clean eye detail, soft key light, subtle rim, premium finish',
    detail: 'Use this when the output needs polish without heavy environmental storytelling.',
  },
  {
    title: 'Environment starter',
    code: 'Product interior, controlled palette, wide framing, structured reflections, cinematic but readable lighting',
    detail: 'Good for scene-building when you still need the subject and composition to stay anchored.',
  },
]

const doList = [
  'Name the subject before describing mood.',
  'Set lighting and framing explicitly when they matter.',
  'Use the negative prompt to remove distortions or clutter.',
  'Save successful outputs and reuse their settings from history.',
]

const dontList = [
  'Do not bury the main subject under stylistic filler.',
  'Do not combine incompatible camera, pose, and scene directions in one line.',
  'Do not raise CFG and size together without a reason.',
  'Do not hide recovery instructions inside the prompt itself.',
]

export default function PromptGuide() {
  return (
    <EditorialFrame
      eyebrow="Prompt Guide"
      title="Master the art of explicit guidance."
      summary="This guide keeps the structure practical: prompt formula, strong starting templates, correction habits, and the small mistakes that usually hurt output quality."
      pills={['Formula first', 'Correction-aware', 'Runtime-friendly']}
    >
      <div className="grid gap-12 xl:grid-cols-[1.1fr_0.9fr] items-start">
        <motion.div 
          variants={container}
          initial="hidden"
          animate="show"
          className="space-y-10"
        >
          <SectionHeading
            title="Quick Rules"
            description="The generator works best when the prompt is explicit, the scene is constrained, and the negative guidance removes likely failures instead of repeating the same mood words."
          />
          
          <div className="grid gap-6">
            {templates.map((template) => (
              <motion.div key={template.title} variants={item}>
                <SurfacePanel className="p-8 space-y-6 hover:border-primary/30 transition-colors">
                  <div className="flex items-center gap-3">
                     <div className="h-8 w-8 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                        <Terminal className="h-4 w-4" />
                     </div>
                     <h3 className="font-display text-2xl font-bold tracking-tight text-foreground dark:text-white">
                       {template.title}
                     </h3>
                  </div>
                  
                  <div className="relative group">
                    <pre className="overflow-x-auto rounded-[24px] bg-secondary/50 dark:bg-black/40 p-6 text-sm font-mono text-primary leading-relaxed border border-border dark:border-white/5">
                      {template.code}
                    </pre>
                  </div>
                  
                  <p className="text-base text-foreground/60 dark:text-white/60 font-medium leading-relaxed">
                    {template.detail}
                  </p>
                </SurfacePanel>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <div className="space-y-10">
          <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
            <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-success px-2">Recommended</h3>
            <ul className="space-y-4">
              {doList.map((text) => (
                <motion.li key={text} variants={item}>
                  <SurfacePanel className="flex gap-4 p-6 border-success/10 bg-success/5 hover:border-success/30 transition-colors">
                    <CheckCircle2 className="h-5 w-5 text-success shrink-0 mt-0.5" />
                    <p className="text-sm font-bold text-foreground/80 dark:text-white/80">{text}</p>
                  </SurfacePanel>
                </motion.li>
              ))}
            </ul>
          </motion.div>

          <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
            <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-danger px-2">To Avoid</h3>
            <ul className="space-y-4">
              {dontList.map((text) => (
                <motion.li key={text} variants={item}>
                  <SurfacePanel className="flex gap-4 p-6 border-danger/10 bg-danger/5 hover:border-danger/30 transition-colors">
                    <XCircle className="h-5 w-5 text-danger shrink-0 mt-0.5" />
                    <p className="text-sm font-bold text-foreground/80 dark:text-white/80">{text}</p>
                  </SurfacePanel>
                </motion.li>
              ))}
            </ul>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
            <SurfacePanel className="p-8 space-y-6 bg-primary/5 border-primary/20">
              <div className="flex items-center gap-3 text-primary">
                <Lightbulb className="h-6 w-6" />
                <h3 className="font-display text-2xl font-bold tracking-tight">Correction Habit</h3>
              </div>
              <p className="text-base text-foreground/70 dark:text-white/70 font-medium leading-relaxed">
                When a result misses the mark, change one variable at a time. Keep the seed when you want a fair comparison,
                and use history to compare prompts, ratio, CFG, and steps instead of editing blindly.
              </p>
            </SurfacePanel>
          </motion.div>
        </div>
      </div>
    </EditorialFrame>
  )
}
