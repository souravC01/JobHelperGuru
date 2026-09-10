import { render, screen, waitFor, act } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from '../App'
import { setAuth, getToken, clearAuth, authFetch } from '../api/client'

describe('Account Switch and State Isolation (S6)', () => {
  it('resets selected resume and closes modals on logout so next account cannot access previous resume', async () => {
    // 1. User A is authenticated with a resume
    const userA = { id: 'user-a-id', email: 'usera@example.test', name: 'User A' }
    setAuth('token-a', userA)

    const resumeA = {
      id: 'resume-a-1',
      name: 'User A Engineering Resume',
      content: 'CONFIDENTIAL USER A WORK EXPERIENCE AND SKILLS',
    }

    globalThis.fetch = vi.fn((url, options) => {
      const u = String(url)
      if (u.includes('/api/auth/me')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(userA),
        })
      }
      if (u.includes('/api/resumes')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve([resumeA]),
        })
      }
      if (u.includes('/api/applications')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve([]),
        })
      }
      if (u.includes('/api/settings')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ use_offline_mode: true }),
        })
      }
      return Promise.reject(new Error(`Unhandled fetch: ${u}`))
    })

    const { unmount } = render(<App />)

    // Wait for User A's data to load
    await waitFor(() => {
      expect(screen.getByText('User A')).toBeInTheDocument()
    })

    // User A logs out
    act(() => {
      clearAuth()
      window.dispatchEvent(new CustomEvent('jh_auth_logout'))
    })

    // 2. User B logs in with zero resumes
    const userB = { id: 'user-b-id', email: 'userb@example.test', name: 'User B' }
    setAuth('token-b', userB)

    globalThis.fetch = vi.fn((url, options) => {
      const u = String(url)
      if (u.includes('/api/auth/me')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(userB),
        })
      }
      if (u.includes('/api/resumes')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve([]), // User B has 0 resumes
        })
      }
      if (u.includes('/api/applications')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve([]),
        })
      }
      if (u.includes('/api/settings')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ use_offline_mode: true }),
        })
      }
      return Promise.reject(new Error(`Unhandled fetch: ${u}`))
    })

    act(() => {
      window.dispatchEvent(new CustomEvent('jh_auth_login_success', { detail: userB }))
    })

    // User A resume content must NOT be present in DOM
    expect(screen.queryByText('CONFIDENTIAL USER A WORK EXPERIENCE AND SKILLS')).not.toBeInTheDocument()

    unmount()
  })

  it('closes modals and resets private state on unauthorized session expiry', async () => {
    const userA = { id: 'user-a-id', email: 'usera@example.test', name: 'User A' }
    setAuth('token-a', userA)

    globalThis.fetch = vi.fn((url) => {
      const u = String(url)
      if (u.includes('/api/auth/me')) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(userA) })
      }
      if (u.includes('/api/resumes') || u.includes('/api/applications')) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve([]) })
      }
      if (u.includes('/api/settings')) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ use_offline_mode: true }) })
      }
      return Promise.reject(new Error(`Unhandled fetch: ${u}`))
    })

    const { unmount } = render(<App />)

    await waitFor(() => {
      expect(screen.getByText('User A')).toBeInTheDocument()
    })

    // Simulate session expiry event
    act(() => {
      window.dispatchEvent(new CustomEvent('jh_auth_unauthorized', { detail: { token: 'token-a' } }))
    })

    // User A must be cleared from state and login modal opened
    await waitFor(() => {
      expect(screen.queryByText('User A')).not.toBeInTheDocument()
      expect(screen.getByText('Welcome to JobHelperGuru')).toBeInTheDocument()
    })

    unmount()
  })

  it('stale delayed response from previous account is discarded and does not overwrite current session', async () => {
    let resolveUserAResumes
    const delayedUserAPromise = new Promise((resolve) => {
      resolveUserAResumes = resolve
    })

    const userA = { id: 'user-a-id', email: 'usera@example.test', name: 'User A' }
    const userB = { id: 'user-b-id', email: 'userb@example.test', name: 'User B' }

    setAuth('token-a', userA)

    globalThis.fetch = vi.fn((url, options) => {
      const u = String(url)
      if (options?.headers?.['Authorization'] === 'Bearer token-a') {
        if (u.includes('/api/resumes')) {
          return delayedUserAPromise
        }
        if (u.includes('/api/auth/me')) {
          return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(userA) })
        }
      }
      if (options?.headers?.['Authorization'] === 'Bearer token-b') {
        if (u.includes('/api/auth/me')) {
          return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(userB) })
        }
        if (u.includes('/api/resumes')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve([{ id: 'resume-b-1', name: 'User B Real Resume', content: 'User B content' }]),
          })
        }
      }
      if (u.includes('/api/applications') || u.includes('/api/settings')) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve([]) })
      }
      return Promise.reject(new Error(`Unhandled fetch: ${u}`))
    })

    const { unmount } = render(<App />)

    // While User A resumes request is in flight, User A logs out and User B logs in
    act(() => {
      clearAuth()
      window.dispatchEvent(new CustomEvent('jh_auth_logout'))
      setAuth('token-b', userB)
      window.dispatchEvent(new CustomEvent('jh_auth_login_success', { detail: userB }))
    })

    // Now User A delayed response returns late
    resolveUserAResumes({
      ok: true,
      status: 200,
      json: () => Promise.resolve([{ id: 'resume-a-stale', name: 'Stale User A Resume', content: 'Stale A' }]),
    })

    // Wait and ensure User B is the active account and User A's stale resume is never shown
    await waitFor(() => {
      expect(screen.getByText('User B')).toBeInTheDocument()
    })

    expect(screen.queryByText('Stale User A Resume')).not.toBeInTheDocument()

    unmount()
  })

  it('stale 401 from previous account does not log out current authenticated user', async () => {
    // User A makes a request with token A
    setAuth('token-a', { id: 'user-a-id', email: 'a@example.test' })

    let resolveStaleResponse
    const stalePromise = new Promise((resolve) => {
      resolveStaleResponse = resolve
    })

    globalThis.fetch = vi.fn((url, options) => {
      // Simulate delayed 401 response for token A
      if (options?.headers?.['Authorization'] === 'Bearer token-a') {
        return stalePromise
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
      })
    })

    // Start request for user A
    const requestA = authFetch('/api/resumes')

    // While request is pending, user A logs out and user B logs in
    setAuth('token-b', { id: 'user-b-id', email: 'b@example.test' })

    // Now User A's stale 401 response arrives
    resolveStaleResponse({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Token expired' }),
    })

    await requestA

    // User B's token must still be intact in storage!
    expect(getToken()).toBe('token-b')
  })
})
