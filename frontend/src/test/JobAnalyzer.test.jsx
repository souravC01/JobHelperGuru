import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import JobAnalyzer from '../components/JobAnalyzer'

describe('JobAnalyzer duplicate URL detection (L10)', () => {
  const existingApplications = [
    {
      id: 'app-1',
      company: 'TechCorp',
      role: 'Backend Engineer',
      status: 'Wishlist',
      url: 'https://careers.techcorp.com/jobs/123',
    },
  ]

  it('displays inline notice when entered URL matches an existing application', () => {
    render(<JobAnalyzer applications={existingApplications} />)

    const input = screen.getByPlaceholderText(/Paste LinkedIn, Greenhouse, Workday/i)
    fireEvent.change(input, { target: { value: 'https://careers.techcorp.com/jobs/123/' } })

    expect(screen.getByText(/Already tracked:/i)).toBeInTheDocument()
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
    expect(screen.getByText('(Backend Engineer)')).toBeInTheDocument()
    expect(screen.getByText('[Wishlist]')).toBeInTheDocument()
  })

  it('does not display inline notice for novel URLs', () => {
    render(<JobAnalyzer applications={existingApplications} />)

    const input = screen.getByPlaceholderText(/Paste LinkedIn, Greenhouse, Workday/i)
    fireEvent.change(input, { target: { value: 'https://careers.newco.com/jobs/456' } })

    expect(screen.queryByText(/Already tracked:/i)).not.toBeInTheDocument()
  })
})
