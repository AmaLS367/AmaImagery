import * as React from 'react'
import { cn } from '../../lib/utils'
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glass?: boolean;
}

export function Card({ className, glass, ...props }: CardProps) {
  return (
    <div 
      className={cn(
        'overflow-hidden rounded-[24px] border text-card-foreground shadow-panel',
        glass ? 'surface-glass' : 'bg-card/92',
        className
      )} 
      {...props} 
    />
  )
}
export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={cn('flex flex-col space-y-1.5 p-6 md:p-7', className)} {...props} /> }
export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) { return <h3 className={cn('font-display text-[28px] font-semibold leading-none tracking-[-0.05em]', className)} {...props} /> }
export function CardDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) { return <p className={cn('text-sm text-muted-foreground', className)} {...props} /> }
export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={cn('p-6 pt-0 md:p-7 md:pt-0', className)} {...props} /> }
export function CardFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={cn('flex items-center p-6 pt-0 md:p-7 md:pt-0', className)} {...props} /> }
