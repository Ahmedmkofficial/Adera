export default function LogoMark({ size = 32, tile = false, title, className, animated = false }) {
  return (
    <svg
      className={className}
      viewBox="0 0 48 48"
      width={size}
      height={size}
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
      focusable="false"
    >
      {tile && <rect width="48" height="48" rx="11" fill="#07131f" />}
      <path
        d="M24 3.2 41 9.4v10.8c0 10.5-6.4 19.2-17 24.6C13.4 39.4 7 30.7 7 20.2V9.4L24 3.2Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinejoin="round"
      />
      <g
        fill="none"
        stroke={tile ? '#e7fbff' : 'var(--logo-line, currentColor)'}
        strokeLinecap="round"
        strokeWidth="1.55"
      >
        <path
          className={animated ? 'ad-login-logo-ridge ad-login-logo-ridge-outer' : undefined}
          d="M14.5 21.4a9.5 9.5 0 0 1 19 0"
          pathLength={animated ? '1' : undefined}
        />
        <path
          className={animated ? 'ad-login-logo-ridge ad-login-logo-ridge-mid' : undefined}
          d="M17.5 21.4a6.5 6.5 0 0 1 13 0"
          pathLength={animated ? '1' : undefined}
        />
        <path
          className={animated ? 'ad-login-logo-ridge ad-login-logo-ridge-core' : undefined}
          d="M20.5 21.4a3.5 3.5 0 0 1 7 0c0 7.1-1.2 11.4-3.5 14.1"
          pathLength={animated ? '1' : undefined}
        />
        <path
          className={animated ? 'ad-login-logo-ridge ad-login-logo-ridge-side' : undefined}
          d="M14.7 25.2c.5 4.3 1.9 7.9 4.3 10.5"
          pathLength={animated ? '1' : undefined}
        />
        <path
          className={animated ? 'ad-login-logo-ridge ad-login-logo-ridge-side' : undefined}
          d="M33.3 25.2c-.4 4.2-1.5 7.5-3.4 10.2"
          pathLength={animated ? '1' : undefined}
        />
        <path
          className={animated ? 'ad-login-logo-ridge ad-login-logo-ridge-center' : undefined}
          d="M24 21.4v8.8"
          pathLength={animated ? '1' : undefined}
        />
      </g>
    </svg>
  )
}
