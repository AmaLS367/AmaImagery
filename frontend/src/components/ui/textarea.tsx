import * as React from 'react'
import { cn } from '../../lib/utils'
export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>
const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, ...props }, ref) => (
  <textarea className={cn('flex min-h-[120px] w-full rounded-[18px] border border-border/70 bg-card/85 px-4 py-3 text-sm text-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] ring-offset-background placeholder:text-muted-foreground/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50', className)} ref={ref} {...props} />
))
Textarea.displayName = 'Textarea'
export { Textarea }
