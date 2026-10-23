import './ui.css'

export default function Button({ children, variant = 'primary', type = 'button', ...props }) {
  return (
    <button type={type} className={`ad-btn ad-btn-${variant}`} {...props}>
      {children}
    </button>
  )
}