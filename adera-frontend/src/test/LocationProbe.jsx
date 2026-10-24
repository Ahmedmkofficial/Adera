import { useLocation } from 'react-router-dom'

export default function LocationProbe() {
  const location = useLocation()
  return <output data-testid="current-path">{location.pathname}</output>
}
