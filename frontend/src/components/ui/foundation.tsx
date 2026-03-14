import type { HTMLAttributes, ReactNode } from 'react'

import { cn } from '../../lib/utils'

export function SectionEyebrow({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return <span className={cn('ui-kicker', className)}>{children}</span>
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
    <div className={cn('space-y-3', className)}>
      <h2 className="ui-heading">{title}</h2>
      {description ? <p className="ui-copy max-w-3xl">{description}</p> : null}
    </div>
  )
}

export function SurfacePanel({
  className,
  glass = false,
  ...props
}: HTMLAttributes<HTMLDivElement> & { glass?: boolean }) {
  return <div className={cn(glass ? 'surface-glass' : 'surface-card', className)} {...props} />
}

export function MetaPill({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return <span className={cn('ui-pill', className)}>{children}</span>
}
