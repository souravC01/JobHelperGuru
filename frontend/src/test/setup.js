import '@testing-library/jest-dom/vitest'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

const rejectNetwork = () => Promise.reject(new Error('Unexpected network request in frontend test'))
globalThis.fetch = vi.fn(rejectNetwork)

afterEach(() => {
  cleanup()
  localStorage.clear()
  sessionStorage.clear()
  document.documentElement.className = ''
  vi.clearAllMocks()
  fetch.mockReset()
  fetch.mockImplementation(rejectNetwork)
})
