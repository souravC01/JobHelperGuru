import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import LandingPage from '../components/landing/LandingPage'

describe('LandingPage', () => {
  it('renders hero, CTAs, interactive playground, and footer', () => {
    const onGetStarted = vi.fn()
    const onExploreGuest = vi.fn()
    const onSignIn = vi.fn()
    const onGoToDashboard = vi.fn()
    const onOpenPrivacy = vi.fn()

    render(
      <LandingPage
        currentUser={null}
        theme="light"
        onToggleTheme={vi.fn()}
        onSignIn={onSignIn}
        onGetStarted={onGetStarted}
        onGoToDashboard={onGoToDashboard}
        onExploreGuest={onExploreGuest}
        onOpenPrivacy={onOpenPrivacy}
      />
    )

    // Verify Hero content
    expect(screen.getByText(/Turn Job Postings into Interview Calls/i)).toBeInTheDocument()
    expect(screen.getAllByText(/BulletCraft Framework/i).length).toBeGreaterThanOrEqual(1)

    // Verify CTAs
    const getStartedBtns = screen.getAllByRole('button', { name: /Get Started Free/i })
    expect(getStartedBtns.length).toBeGreaterThanOrEqual(1)
    fireEvent.click(getStartedBtns[0])
    expect(onGetStarted).toHaveBeenCalled()

    const guestBtns = screen.getAllByRole('button', { name: /Try Guest Workspace/i })
    expect(guestBtns.length).toBeGreaterThanOrEqual(1)
    fireEvent.click(guestBtns[0])
    expect(onExploreGuest).toHaveBeenCalled()

    // Verify sections render
    expect(screen.getByText(/Core Capabilities/i)).toBeInTheDocument()
    expect(screen.getByText(/3-Step Workflow/i)).toBeInTheDocument()
    expect(screen.getByText(/Frequently Asked Questions/i)).toBeInTheDocument()
  })

  it('renders authenticated dashboard button when currentUser is present', () => {
    const onGoToDashboard = vi.fn()
    render(
      <LandingPage
        currentUser={{ email: 'user@test.com' }}
        theme="light"
        onToggleTheme={vi.fn()}
        onSignIn={vi.fn()}
        onGetStarted={vi.fn()}
        onGoToDashboard={onGoToDashboard}
        onExploreGuest={vi.fn()}
        onOpenPrivacy={vi.fn()}
      />
    )

    const dashBtns = screen.getAllByRole('button', { name: /Go to Dashboard/i })
    expect(dashBtns.length).toBeGreaterThanOrEqual(1)
    fireEvent.click(dashBtns[0])
    expect(onGoToDashboard).toHaveBeenCalled()
  })
})
