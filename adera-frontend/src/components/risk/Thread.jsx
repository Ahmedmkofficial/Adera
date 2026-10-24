import { levelClass } from '../../utils/risk'

export default function Thread({ items, level }) {
  return (
    <ul className={`rk-thread ${levelClass(level)}`}>
      {items.map((item) => (
        <li key={item}>
          <span className="rk-node" aria-hidden="true" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  )
}