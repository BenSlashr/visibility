import React, { useState, useRef } from 'react'

interface TooltipProps {
  text: string
  children: React.ReactNode
  position?: 'top' | 'bottom' | 'left' | 'right'
}

export const Tooltip: React.FC<TooltipProps> = ({ text, children, position = 'top' }) => {
  const [visible, setVisible] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  return (
    <div
      ref={ref}
      className="relative inline-block"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div
          className={`absolute z-50 px-2 py-1 text-xs text-white bg-gray-900/90 backdrop-blur border border-gray-800/80 rounded shadow transition-opacity duration-150 ${
            position === 'top' ? 'bottom-full mb-2 left-1/2 -translate-x-1/2' :
            position === 'bottom' ? 'top-full mt-2 left-1/2 -translate-x-1/2' :
            position === 'left' ? 'right-full mr-2 top-1/2 -translate-y-1/2' :
            'left-full ml-2 top-1/2 -translate-y-1/2'
          }`}
          role="tooltip"
        >
          {text}
        </div>
      )}
    </div>
  )
}


