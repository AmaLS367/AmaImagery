import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'
const buttonVariants = cva('inline-flex items-center justify-center rounded-[18px] border border-transparent text-sm font-semibold tracking-[-0.02em] transition-[transform,colors,box-shadow] duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ring-offset-background', {
  variants: {
    variant: {
      default: 'bg-primary text-primary-foreground shadow-glow hover:-translate-y-0.5 hover:bg-primary/90',
      secondary: 'border-border/70 bg-card/85 text-card-foreground shadow-panel hover:-translate-y-0.5 hover:bg-card',
      outline: 'border-border/70 bg-transparent text-foreground hover:border-primary/40 hover:bg-primary/10',
      ghost: 'border-transparent bg-transparent text-foreground/75 hover:bg-card/70 hover:text-foreground',
      link: 'underline-offset-4 hover:underline text-primary',
    },
    size: { default: 'h-11 px-5 py-2.5', sm: 'h-9 px-4 text-xs', lg: 'h-12 px-6 text-base', icon: 'h-11 w-11' },
  },
  defaultVariants: { variant: 'default', size: 'default' },
})
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> { asChild?: boolean }
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : 'button'
  const type = asChild ? undefined : (props.type ?? 'button')
  return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} type={type} {...props} /> 
})
Button.displayName = 'Button'
export { Button, buttonVariants }
