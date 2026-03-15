import * as React from 'react'
import * as SwitchPr from '@radix-ui/react-switch'
import { cn } from '../../lib/utils'
const Switch = React.forwardRef<React.ElementRef<typeof SwitchPr.Root>, React.ComponentPropsWithoutRef<typeof SwitchPr.Root>>(({ className, ...props }, ref) => (
  <SwitchPr.Root ref={ref} className={cn('peer inline-flex h-7 w-12 shrink-0 cursor-pointer items-center rounded-full border border-border/70 bg-card/80 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:border-primary/40 data-[state=unchecked]:bg-secondary', className)} {...props}>
    <SwitchPr.Thumb className="pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-[22px] data-[state=unchecked]:translate-x-[4px]" />
  </SwitchPr.Root>
))
Switch.displayName = 'Switch'
export { Switch }
