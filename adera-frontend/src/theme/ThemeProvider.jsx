import { useCallback, useLayoutEffect, useMemo, useState } from 'react'
import { ThemeContext } from './ThemeContext'

export const THEME_KEY = 'adera.theme'

function readTheme() {
  try {
    return localStorage.getItem(THEME_KEY) === 'light' ? 'light' : 'dark'
  } catch {
    return 'dark'
  }
}

export default function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(readTheme)

  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme
    const themeColor = document.querySelector('meta[name="theme-color"]')
    if (themeColor) {
      themeColor.setAttribute('content', theme === 'dark' ? '#07131f' : '#edf4f7')
    }
    try {
      localStorage.setItem(THEME_KEY, theme)
    } catch {
      // The current page still uses the selected theme if storage is unavailable.
    }
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme((current) => (current === 'dark' ? 'light' : 'dark'))
  }, [])

  const value = useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme])
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
