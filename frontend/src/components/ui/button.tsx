import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'
const buttonVariants = cva('runtime-button inline-flex items-center justify-center border border-transparent text-sm font-semibold tracking-[-0.02em] transition-[transform,colors,box-shadow] duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ring-offset-background', {
  variants: {
    variant: {
      default: 'runtime-button-default hover:-translate-y-0.5 hover:brightness-105',
      secondary: 'runtime-button-secondary hover:-translate-y-0.5 hover:brightness-105',
      outline: 'runtime-button-outline text-foreground hover:border-primary/40',
      ghost: 'runtime-button-ghost border-transparent bg-transparent text-foreground/75 hover:text-foreground',
      link: 'border-transparent bg-transparent underline-offset-4 hover:underline text-primary',
    },
    size: {
      default: 'ui-button-size-default py-2.5',
      sm: 'ui-button-size-sm px-4 text-xs',
      lg: 'ui-button-size-lg text-base',
      icon: 'ui-button-size-icon',
    },
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
