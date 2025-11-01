import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'

import { cn } from '@/lib/utils'

const STORAGE_KEY = 'kasm-theme-preference'

type ThemeMode = 'light' | 'dark'

const getInitialTheme = (): ThemeMode => {
  if (typeof window === 'undefined') {
    return 'dark'
  }

  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') {
    return stored
  }

  return 'dark'
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const initial = getInitialTheme()
    if (typeof document !== 'undefined') {
      document.documentElement.classList.toggle('dark', initial === 'dark')
    }
    return initial
  })

  useEffect(() => {
    if (typeof document === 'undefined') {
      return
    }

    const root = document.documentElement
    root.classList.toggle('dark', theme === 'dark')
    window.localStorage.setItem(STORAGE_KEY, theme)
  }, [theme])

  const handleToggle = () => {
    setTheme((current) => (current === 'dark' ? 'light' : 'dark'))
  }

  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      onClick={handleToggle}
      className="relative inline-flex h-7 w-12 items-center rounded-full border border-border bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    >
      <span
        className={cn(
          'absolute left-1 flex h-5 w-5 items-center justify-center rounded-full bg-card text-foreground shadow transition-transform',
          isDark ? 'translate-x-5' : 'translate-x-0',
        )}
      >
        {isDark ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
      </span>
      <span className="sr-only">Toggle color theme</span>
    </button>
  )
}
