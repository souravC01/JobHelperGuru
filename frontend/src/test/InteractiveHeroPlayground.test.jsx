import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import InteractiveHeroPlayground from '../components/landing/InteractiveHeroPlayground'

describe('InteractiveHeroPlayground', () => {
  it('renders all 4 tabs and defaults to BulletCraft tab', () => {
    render(<InteractiveHeroPlayground onTryLiveDemo={vi.fn()} />)
    expect(screen.getByRole('tab', { name: /BulletCraft/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /ATS Fit Matcher/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Job Scraper/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Pipeline CRM/i })).toBeInTheDocument()
    expect(screen.getByText(/Responsible for writing backend APIs/i)).toBeInTheDocument()
  })

  it('transforms weak bullet into BulletCraft formula with XYZ badges', () => {
    render(<InteractiveHeroPlayground onTryLiveDemo={vi.fn()} />)
    const transformBtn = screen.getByRole('button', { name: /Transform with BulletCraft/i })
    fireEvent.click(transformBtn)
    expect(screen.getByText(/Accomplished \[X\]/i)).toBeInTheDocument()
    expect(screen.getByText(/Measured by \[Y\]/i)).toBeInTheDocument()
    expect(screen.getByText(/Done by \[Z\]/i)).toBeInTheDocument()
    expect(screen.getByText(/Engineered 14 resilient FastAPI microservices/i)).toBeInTheDocument()
  })

  it('switches to ATS Matcher tab and allows skill adoption', () => {
    render(<InteractiveHeroPlayground onTryLiveDemo={vi.fn()} />)
    fireEvent.click(screen.getByRole('tab', { name: /ATS Fit Matcher/i }))
    expect(screen.getByText(/ATS Match Score/i)).toBeInTheDocument()
    expect(screen.getByText(/88%/i)).toBeInTheDocument()
    const adoptBtn = screen.getByRole('button', { name: /Adopt Missing Skill/i })
    fireEvent.click(adoptBtn)
    expect(screen.getByText(/96%/i)).toBeInTheDocument()
  })

  it('switches to Job Scraper tab and displays parsed job fields', () => {
    render(<InteractiveHeroPlayground onTryLiveDemo={vi.fn()} />)
    fireEvent.click(screen.getByRole('tab', { name: /Job Scraper/i }))
    expect(screen.getByText(/Senior Software Engineer/i)).toBeInTheDocument()
    expect(screen.getByText(/\$140,000 - \$175,000/i)).toBeInTheDocument()
    expect(screen.getByText(/Eligible: 2024-2026 Graduates/i)).toBeInTheDocument()
  })

  it('switches to Pipeline CRM tab and advances Kanban card', () => {
    render(<InteractiveHeroPlayground onTryLiveDemo={vi.fn()} />)
    fireEvent.click(screen.getByRole('tab', { name: /Pipeline CRM/i }))
    expect(screen.getByText(/Stripe - Senior Infrastructure Engineer/i)).toBeInTheDocument()
    const moveBtn = screen.getByRole('button', { name: /Advance to Interviewing/i })
    fireEvent.click(moveBtn)
    expect(screen.getByText(/Current Status:/i)).toHaveTextContent('Interviewing')
  })

  it('calls onTryLiveDemo when the live demo button is clicked', () => {
    const onTryLiveDemo = vi.fn()
    render(<InteractiveHeroPlayground onTryLiveDemo={onTryLiveDemo} />)
    const demoBtn = screen.getByRole('button', { name: /Launch Live in Workspace/i })
    fireEvent.click(demoBtn)
    expect(onTryLiveDemo).toHaveBeenCalledTimes(1)
  })
})
