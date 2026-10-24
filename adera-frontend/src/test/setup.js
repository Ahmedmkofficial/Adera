import '@testing-library/jest-dom/vitest'
import { cleanup, configure } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

// The mock backend answers after a short fake delay, so give lookups a bit longer.
configure({ asyncUtilTimeout: 4000 })

// jsdom is missing two browser features that React Flow needs.
globalThis.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.DOMMatrixReadOnly = class {
  constructor() {
    this.m22 = 1
  }
}
window.scrollTo = () => {}

beforeEach(() => {
  sessionStorage.clear()
  localStorage.clear()
})

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.unstubAllEnvs()
})
