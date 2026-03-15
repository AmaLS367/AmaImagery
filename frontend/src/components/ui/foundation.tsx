import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/utils'

export function SectionEyebrow({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div className={cn(
      "text-[10px] font-black uppercase tracking-[0.3em] text-primary mb-2",
      className
    )}>
      {children}
    </div>
  )
}

export function SectionHeading({
  title,
  description,
  className,
}: {
  title: ReactNode
  description?: ReactNode
  className?: string
}) {
  return (
    <div className={cn("space-y-4", className)}>
      <h2 className="font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
        {title}
      </h2>
      {description && (
        <p className="max-w-2xl text-base leading-relaxed text-foreground/60 dark:text-white/60 font-medium">
          {description}
        </p>
      )}
    </div>
  )
}

export function SurfacePanel({
  className,
  glass = false,
  ...props
}: HTMLAttributes<HTMLDivElement> & { glass?: boolean }) {
  return (
    <div 
      className={cn(
        "runtime-surface transition-all duration-300",
        glass && "runtime-surface--glass",
        className
      )} 
      {...props} 
    />
  )
}

export function MetaPill({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div className={cn(
      "ui-pill inline-flex items-center gap-2 px-4 py-1.5 text-[10px] font-black uppercase tracking-[0.2em]",
      className
    )}>
      <div className="h-1.5 w-1.5 rounded-full bg-primary" />
      {children}
    </div>
  )
}
