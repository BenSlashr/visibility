import React from 'react'

interface ToggleProps {
  enabled: boolean
  onChange: (enabled: boolean) => void
  label?: string
  description?: string
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export const Toggle: React.FC<ToggleProps> = ({
  enabled,
  onChange,
  label,
  description,
  disabled = false,
  size = 'md'
}) => {
  const sizeClasses = {
    sm: {
      switch: 'h-4 w-7',
      knob: 'h-3 w-3',
      translate: enabled ? 'translate-x-3' : 'translate-x-0'
    },
    md: {
      switch: 'h-6 w-11',
      knob: 'h-5 w-5',
      translate: enabled ? 'translate-x-5' : 'translate-x-0.5'
    },
    lg: {
      switch: 'h-7 w-14',
      knob: 'h-6 w-6',
      translate: enabled ? 'translate-x-7' : 'translate-x-0.5'
    }
  }

  const classes = sizeClasses[size]

  return (
    <div className="flex items-start">
      <div className="flex items-center">
        <button
          type="button"
          onClick={() => !disabled && onChange(!enabled)}
          disabled={disabled}
          className={`
            ${classes.switch}
            relative inline-flex shrink-0 cursor-pointer rounded-full border-2 border-transparent 
            transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2
            ${enabled ? 'bg-blue-600' : 'bg-gray-200'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          role="switch"
          aria-checked={enabled}
        >
          <span
            aria-hidden="true"
            className={`
              ${classes.knob}
              pointer-events-none inline-block rounded-full bg-white shadow transform ring-0 
              transition duration-200 ease-in-out
              ${classes.translate}
            `}
          />
        </button>
      </div>
      
      {(label || description) && (
        <div className="ml-3">
          {label && (
            <label className={`text-sm font-medium ${disabled ? 'text-gray-400' : 'text-gray-900'}`}>
              {label}
            </label>
          )}
          {description && (
            <p className={`text-sm ${disabled ? 'text-gray-300' : 'text-gray-500'}`}>
              {description}
            </p>
          )}
        </div>
      )}
    </div>
  )
} 