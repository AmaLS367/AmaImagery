import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  AlertTriangle,
  Check,
  ChevronDown,
  ChevronUp,
  Copy,
  RefreshCw,
  XCircle,
  Cpu,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from './ui/button'
import { cn } from '../lib/utils'

export type GenerationErrorStateProps = {
  error: string
  tone?: 'dashboard' | 'editorial' | 'cinematic'
  onRetry?: () => void
  onDismiss?: () => void
  className?: string
}

function getErrorAdvice(error: string): string | null {
  const lower = error.toLowerCase()
  if (lower.includes('modelmmap') || lower.includes('allocation failed') || lower.includes('out of memory') || lower.includes('cuda out of memory') || lower.includes('oom')) {
    return 'GPU memory allocation failure. Try reducing image dimensions or steps.'
  }
  if (lower.includes('timed out') || lower.includes('timeout')) {
    return 'The generation worker took too long to respond. The queue may be overloaded.'
  }
  if (lower.includes('connection refused') || lower.includes('network') || lower.includes('failed to fetch')) {
    return 'Network connection issue to the generation service. Check your server connection.'
  }
  return null
}

export function GenerationErrorState({
  error,
  tone = 'dashboard',
  onRetry,
  onDismiss,
  className,
}: GenerationErrorStateProps) {
  const { t } = useTranslation(['generate', 'common'])
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  const advice = getErrorAdvice(error)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(error)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // ignore clipboard error
    }
  }

  const isCinematic = tone === 'cinematic'

  return (
    <motion.div
      key="generation-error-state"
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.25 }}
      className={cn(
        'flex w-full min-h-[360px] flex-col items-center justify-center p-6 sm:p-8 text-center',
        className,
      )}
    >
      <div className="mx-auto flex max-w-md flex-col items-center space-y-4">
        {/* Error icon badge */}
        <div
          className={cn(
            'flex h-16 w-16 items-center justify-center rounded-3xl border shadow-lg transition-transform',
            isCinematic
              ? 'border-red-500/30 bg-red-500/10 text-red-400 shadow-red-500/10'
              : 'border-danger/30 bg-danger/10 text-danger shadow-danger/10',
          )}
        >
          <AlertTriangle className="h-8 w-8" />
        </div>

        {/* Title & human-readable message */}
        <div className="space-y-2">
          <h4
            className={cn(
              'text-lg font-bold tracking-tight sm:text-xl',
              isCinematic ? 'text-white' : 'text-foreground',
            )}
          >
            {t('generate:error_state.title', 'Generation Failed')}
          </h4>
          <p
            className={cn(
              'text-sm leading-relaxed',
              isCinematic ? 'text-white/70' : 'text-foreground/70',
            )}
          >
            {advice || t('generate:error_state.subtitle', 'The backend encountered an error while processing the image.')}
          </p>
        </div>

        {/* Technical details toggle & content */}
        <div className="w-full max-w-sm space-y-2 text-left">
          <button
            type="button"
            onClick={() => setDetailsOpen((prev) => !prev)}
            className={cn(
              'flex w-full items-center justify-between rounded-xl px-3 py-2 text-xs font-semibold transition-colors',
              isCinematic
                ? 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white'
                : 'bg-secondary/30 text-foreground/60 hover:bg-secondary/50 hover:text-foreground',
            )}
          >
            <span className="flex items-center gap-1.5">
              <Cpu className="h-3.5 w-3.5 text-danger" />
              {detailsOpen
                ? t('generate:error_state.details_toggle_hide', 'Hide technical details')
                : t('generate:error_state.details_toggle_show', 'Show technical details')}
            </span>
            {detailsOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>

          {detailsOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className={cn(
                'relative overflow-hidden rounded-2xl border p-3 text-xs',
                isCinematic
                  ? 'border-white/10 bg-black/60 text-red-300'
                  : 'border-danger/20 bg-danger/5 text-danger',
              )}
            >
              <div className="flex items-center justify-between pb-2 border-b border-border/20 mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider opacity-60">Log output</span>
                <button
                  type="button"
                  onClick={handleCopy}
                  className={cn(
                    'flex items-center gap-1 text-[10px] font-medium transition-colors px-2 py-0.5 rounded-md',
                    isCinematic
                      ? 'bg-white/10 hover:bg-white/20 text-white'
                      : 'bg-secondary hover:bg-secondary/80 text-foreground',
                  )}
                >
                  {copied ? (
                    <>
                      <Check className="h-3 w-3 text-green-400" />
                      <span>{t('generate:error_state.copied', 'Copied!')}</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      <span>{t('generate:error_state.copy_details', 'Copy')}</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="max-h-36 overflow-x-auto overflow-y-auto whitespace-pre-wrap break-all font-mono text-[11px] leading-relaxed select-text">
                {error}
              </pre>
            </motion.div>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          {onRetry && (
            <Button
              variant="default"
              size="sm"
              onClick={onRetry}
              className="rounded-full shadow-md"
            >
              <RefreshCw className="mr-2 h-3.5 w-3.5" />
              {t('generate:error_state.retry', 'Retry')}
            </Button>
          )}
          {onDismiss && (
            <Button
              variant="outline"
              size="sm"
              onClick={onDismiss}
              className="rounded-full"
            >
              <XCircle className="mr-2 h-3.5 w-3.5" />
              {t('generate:error_state.dismiss', 'Dismiss')}
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  )
}
