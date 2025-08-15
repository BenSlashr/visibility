import React, { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'

export const ThemeToggle: React.FC = () => {
  const [dark, setDark] = useState(false)

  useEffect(() => {
    const isDark = document.documentElement.classList.contains('dark')
    setDark(isDark)
  }, [])

  const toggle = () => {
    const next = !dark
    setDark(next)
    document.documentElement.classList.toggle('dark', next)
    try {
      localStorage.setItem('theme', next ? 'dark' : 'light')
    } catch {}
  }

  useEffect(() => {
    try {
      const saved = localStorage.getItem('theme')
      if (saved) {
        const isDark = saved === 'dark'
        document.documentElement.classList.toggle('dark', isDark)
        setDark(isDark)
      }
    } catch {}
  }, [])

  return (
    <button
      onClick={toggle}
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-200 dark:border-gray-700 dark:hover:bg-gray-800/60 backdrop-blur"
      aria-label="Basculer le thème"
      title="Basculer le thème"
    >
      {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      <span className="hidden sm:inline">{dark ? 'Clair' : 'Sombre'}</span>
    </button>
  )
}


