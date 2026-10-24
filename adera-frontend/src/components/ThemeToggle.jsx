import { useTheme } from '../theme/useTheme'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const nextTheme = theme === 'dark' ? 'light' : 'dark'

  return (
    <button
      type="button"
      className="ad-theme-toggle"
      onClick={toggleTheme}
      aria-label={`Switch to ${nextTheme} theme`}
      title={`Switch to ${nextTheme} theme`}
    >
      <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
        {theme === 'dark' ? (
          <>
            <circle cx="10" cy="10" r="3.2" />
            <path d="M10 1.8v2M10 16.2v2M18.2 10h-2M3.8 10h-2m14-5.8-1.4 1.4M5.6 14.4l-1.4 1.4m11.6 0-1.4-1.4M5.6 5.6 4.2 4.2" />
          </>
        ) : (
          <path d="M16.8 12.5A7 7 0 0 1 7.5 3.2 7.2 7.2 0 1 0 16.8 12.5Z" />
        )}
      </svg>
      <span>{nextTheme === 'light' ? 'Light' : 'Dark'}</span>
    </button>
  )
}
