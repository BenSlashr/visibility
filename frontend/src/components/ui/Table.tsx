import React from 'react'
import { clsx } from 'clsx'

interface Column {
  key: string
  label: string
  className?: string
  render?: (row: Record<string, any>) => React.ReactNode
}

interface TableProps {
  columns: Column[]
  data: Record<string, any>[]
  className?: string
  onRowClick?: (row: Record<string, any>) => void
}

export const Table: React.FC<TableProps> = ({
  columns,
  data,
  className,
  onRowClick
}) => {
  return (
    <div className={clsx('overflow-hidden border border-gray-200 rounded-lg dark:border-gray-800/80 backdrop-blur', className)}>
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800/80">
        {/* Header */}
        <thead className="bg-gray-50 dark:bg-gray-900/60">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={clsx(
                  'px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider',
                  column.className
                )}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        
        {/* Body */}
        <tbody className="bg-white dark:bg-gray-900/40 divide-y divide-gray-200 dark:divide-gray-800/60">
          {data.map((row, index) => (
            <tr
              key={index}
              className={clsx(
                'hover:bg-gray-50 dark:hover:bg-gray-800/40 transition-colors',
                onRowClick && 'cursor-pointer'
              )}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={clsx(
                    "px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100",
                    column.className
                  )}
                >
                  {column.render ? column.render(row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      
      {data.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">Aucune donnée à afficher</p>
        </div>
      )}
    </div>
  )
} 