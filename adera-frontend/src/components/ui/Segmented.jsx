import './ui.css'

export default function Segmented({ items, value, onChange, label }) {
  return (
    <div className="ad-seg" role="group" aria-label={label}>
      {items.map((item) => (
        <button
          key={item}
          type="button"
          aria-pressed={value === item}
          onClick={() => onChange(item)}
        >
          {item}
        </button>
      ))}
    </div>
  )
}