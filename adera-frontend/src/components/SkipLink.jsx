// Lets keyboard users jump past the navigation straight to the page content.
export default function SkipLink() {
  function jump(e) {
    e.preventDefault()
    document.getElementById('main')?.focus()
  }
  return (
    <a className="skip-link" href="#main" onClick={jump}>
      Skip to content
    </a>
  )
}
