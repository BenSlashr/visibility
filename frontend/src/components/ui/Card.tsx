import React from 'react'
import { clsx } from 'clsx'

interface CardProps {
  children: React.ReactNode
  className?: string
  padding?: 'sm' | 'md' | 'lg'
  shadow?: 'sm' | 'md' | 'lg'
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  padding = 'md',
  shadow = 'sm'
}) => {
  return (
    <div
      className={clsx(
        'bg-gray-50 rounded-lg border border-gray-200 dark:bg-gray-900/60 dark:border-gray-800/80',
        {
          'p-4': padding === 'sm',
          'p-6': padding === 'md',
          'p-8': padding === 'lg',
        },
        {
          'shadow-sm dark:shadow-none': shadow === 'sm',
          'shadow-md dark:shadow-[0_0_0_1px_rgba(17,24,39,0.6)]': shadow === 'md',
          'shadow-lg dark:shadow-[0_0_0_1px_rgba(17,24,39,0.8)]': shadow === 'lg',
        },
        className
      )}
    >
      {children}
    </div>
  )
} 