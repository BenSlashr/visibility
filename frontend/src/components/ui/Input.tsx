import React from 'react'
import { clsx } from 'clsx'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  variant?: 'default' | 'error' | 'success'
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  variant = 'default',
  className,
  ...props
}) => {
  const inputVariant = error ? 'error' : variant

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label}
        </label>
      )}
      
      <input
        className={clsx(
          'w-full px-3 py-2 border rounded-md text-sm transition-colors bg-white text-gray-900',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          {
            'border-gray-300': inputVariant === 'default',
            'border-red-300 focus:border-red-500 focus:ring-red-500': inputVariant === 'error',
            'border-green-300 focus:border-green-500 focus:ring-green-500': inputVariant === 'success',
          },
          className
        )}
        {...props}
      />
      
      {(error || helperText) && (
        <p className={clsx(
          'mt-1 text-xs',
          error ? 'text-red-600' : 'text-gray-500 dark:text-gray-400'
        )}>
          {error || helperText}
        </p>
      )}
    </div>
  )
} 