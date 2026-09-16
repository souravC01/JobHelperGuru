import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from '../App'

describe('App Routing', () => {
  beforeEach(() => {
    window.history.pushState(null, '', '/')
  })

  it('renders LandingPage by default at /', async () => {
    render(<App />)
    expect(screen.getByText(/Turn Job Postings into Interview Calls/i)).toBeInTheDocument()
    expect(screen.getByText(/Core Capabilities/i)).toBeInTheDocument()
  })

  it('navigates to /app when clicking Try Guest Workspace', async () => {
    render(<App />)
    const guestBtn = screen.getAllByRole('button', { name: /Try Guest Workspace/i })[0]
    fireEvent.click(guestBtn)
    await waitFor(() => {
      expect(window.location.pathname).toBe('/app')
      expect(screen.getByRole('button', { name: /Job Analyzer/i })).toBeInTheDocument()
    })
  })

  it('navigates back to / when clicking brand logo from /app', async () => {
    window.history.pushState(null, '', '/app')
    render(<App />)
    expect(screen.getByRole('button', { name: /Job Analyzer/i })).toBeInTheDocument()
    const brandLogo = screen.getByTestId('brand-logo')
    fireEvent.click(brandLogo)
    await waitFor(() => {
      expect(window.location.pathname).toBe('/')
      expect(screen.getByText(/Turn Job Postings into Interview Calls/i)).toBeInTheDocument()
    })
  })

  it('opens AuthModal from landing page when clicking Get Started Free', async () => {
    render(<App />)
    const getStartedBtn = screen.getAllByRole('button', { name: /Get Started Free/i })[0]
    fireEvent.click(getStartedBtn)
    await waitFor(() => {
      expect(screen.getByText(/Create Account/i)).toBeInTheDocument()
    })
  })
})
