import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import LandingNav from '../components/landing/LandingNav'
import ValuePillars from '../components/landing/ValuePillars'
import HowItWorks from '../components/landing/HowItWorks'
import FaqSection from '../components/landing/FaqSection'
import LandingFooter from '../components/landing/LandingFooter'

describe('Landing Subcomponents', () => {
  it('LandingNav displays Sign In and Get Started when unauthenticated', () => {
    const onSignIn = vi.fn()
    const onGetStarted = vi.fn()
    render(
      <LandingNav
        currentUser={null}
        onSignIn={onSignIn}
        onGetStarted={onGetStarted}
        onGoToDashboard={vi.fn()}
        theme="light"
        onToggleTheme={vi.fn()}
      />
    )
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Get Started Free/i })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }))
    expect(onSignIn).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: /Get Started Free/i }))
    expect(onGetStarted).toHaveBeenCalledTimes(1)
  })

  it('LandingNav displays Go to Dashboard when authenticated', () => {
    const onGoToDashboard = vi.fn()
    render(
      <LandingNav
        currentUser={{ email: 'user@test.com' }}
        onSignIn={vi.fn()}
        onGetStarted={vi.fn()}
        onGoToDashboard={onGoToDashboard}
        theme="light"
        onToggleTheme={vi.fn()}
      />
    )
    expect(screen.getByRole('button', { name: /Go to Dashboard/i })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Go to Dashboard/i }))
    expect(onGoToDashboard).toHaveBeenCalledTimes(1)
  })

  it('ValuePillars renders 4 core pillars', () => {
    render(<ValuePillars />)
    expect(screen.getByText(/Multi-Format Job Scraping/i)).toBeInTheDocument()
    expect(screen.getByText(/Context-Aware Fact Verification/i)).toBeInTheDocument()
    expect(screen.getByText(/Recruiter Outreach Generator/i)).toBeInTheDocument()
    expect(screen.getByText(/Enterprise Security & BYOK/i)).toBeInTheDocument()
  })

  it('HowItWorks renders 3 workflow steps', () => {
    render(<HowItWorks />)
    expect(screen.getByText(/Parse the True Requirements/i)).toBeInTheDocument()
    expect(screen.getByText(/Optimize Bullets & Pick the Best Resume/i)).toBeInTheDocument()
    expect(screen.getByText(/Track Deadlines & Export to Excel/i)).toBeInTheDocument()
  })

  it('FaqSection toggles answers on click', () => {
    render(<FaqSection />)
    const question = screen.getByText(/Is JobHelperGuru free to use\?/i)
    fireEvent.click(question)
    expect(screen.getByText(/100% free offline heuristic NLP mode/i)).toBeInTheDocument()
  })

  it('LandingFooter triggers privacy modal', () => {
    const onOpenPrivacy = vi.fn()
    render(<LandingFooter onOpenPrivacy={onOpenPrivacy} />)
    fireEvent.click(screen.getByRole('button', { name: /Privacy & Terms/i }))
    expect(onOpenPrivacy).toHaveBeenCalledTimes(1)
  })
})
