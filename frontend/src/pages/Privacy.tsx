import { motion } from 'framer-motion'
import { EditorialFrame } from '../components/editorial/EditorialFrame'
import { SurfacePanel, SectionHeading } from '../components/ui/foundation'

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

const sections = [
  {
    title: 'What we collect',
    body: 'AmaImagery stores account identifiers, authentication state, generation prompts, runtime metadata, shell settings, and the resulting media records required to operate the product.',
  },
  {
    title: 'Why we collect it',
    body: 'The data is used to authenticate users, deliver generation results, preserve searchable history, apply shell preferences, support moderation defaults, and investigate service issues when something fails.',
  },
  {
    title: 'Retention and visibility',
    body: 'History depth follows the configured archive limit. Settings remain attached to the account so shell behavior, notification rules, and safety defaults are preserved between sessions.',
  },
  {
    title: 'Operational security',
    body: 'We apply access controls, scoped credentials, and environment-level protections appropriate for a creator tool that handles prompts, generated assets, and account recovery flows.',
  },
  {
    title: 'Your controls',
    body: 'You can change shell preferences, notification behavior, history depth, safety defaults, and language from Settings. Account recovery remains available through the dedicated auth routes.',
  },
  {
    title: 'Contact',
    body: 'Questions about privacy or data handling can be sent to privacy@amaimagery.com.',
  },
]

export default function Privacy() {
  return (
    <EditorialFrame
      eyebrow="Privacy Policy"
      title="How we handle your data with professional care."
      summary="Learn about the data AmaImagery collects, why it's needed, and the controls available to you."
      pills={['Last updated March 14, 2026', 'Operational data only', 'Account controls']}
    >
      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
      >
        {sections.map((section) => (
          <motion.div key={section.title} variants={item}>
            <SurfacePanel className="h-full p-8 space-y-4 hover:border-primary/30 transition-colors">
              <h3 className="font-display text-2xl font-bold tracking-tight text-foreground dark:text-white">
                {section.title}
              </h3>
              <p className="text-base text-foreground/60 dark:text-white/60 leading-relaxed">
                {section.body}
              </p>
            </SurfacePanel>
          </motion.div>
        ))}
      </motion.div>
    </EditorialFrame>
  )
}
