// The Adera mark: three rings and a dot. Geometry and colors come from the logo file.
// `tile` adds the rounded paper square (for icons); without it the rings sit on the page.
export default function LogoMark({ size = 32, tile = false, title, className }) {
  return (
    <svg
      className={className}
      viewBox={tile ? '0 0 512 512' : '64 64 384 384'}
      width={size}
      height={size}
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
      focusable="false"
    >
      {tile && <rect width="512" height="512" rx="112" fill="#f6f5f1" />}
      <circle cx="256" cy="256" r="176" fill="none" stroke="#aaa9a8" strokeWidth="24" />
      <circle cx="256" cy="256" r="112" fill="none" stroke="#1c1c1e" strokeWidth="24" />
      <circle cx="256" cy="256" r="44" fill="#d9622b" />
    </svg>
  )
}
