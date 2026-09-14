import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import JobAnalyzer from '../components/JobAnalyzer'
import { analyzeJob } from '../api/client'

vi.mock('../api/client', () => ({
  analyzeJob: vi.fn(),
  addApplication: vi.fn(),
}))

describe('JobAnalyzer input modes', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('disables link controls while raw text is open and preserves drafts when switching', () => {
    render(<JobAnalyzer />)
    const url = screen.getByPlaceholderText(/Paste LinkedIn/)
    const analyzeUrl = screen.getByRole('button', { name: 'Analyze Job', exact: true })
    fireEvent.change(url, { target: { value: 'https://example.com/job' } })
    fireEvent.click(screen.getByRole('button', { name: 'Or Paste Job Text Directly' }))
    expect(url).toBeDisabled()
    expect(analyzeUrl).toBeDisabled()

    const text = screen.getByPlaceholderText('Paste full job description text here...')
    fireEvent.change(text, { target: { value: 'Backend engineer with Python experience.' } })
    expect(screen.getByRole('button', { name: 'Analyze Raw Text' })).toBeEnabled()
    fireEvent.click(screen.getByRole('button', { name: 'Hide Text Area' }))
    expect(url).toBeEnabled()
    expect(analyzeUrl).toBeEnabled()
    expect(url).toHaveValue('https://example.com/job')
    expect(screen.queryByRole('button', { name: 'Analyze Raw Text' })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Or Paste Job Text Directly' }))
    expect(screen.getByPlaceholderText('Paste full job description text here...')).toHaveValue('Backend engineer with Python experience.')
  })

  it('sends only raw text when Analyze Raw Text is clicked', async () => {
    analyzeJob.mockResolvedValue({ title: 'Backend Engineer' })
    render(<JobAnalyzer />)
    fireEvent.change(screen.getByPlaceholderText(/Paste LinkedIn/), { target: { value: 'https://example.com/job' } })
    fireEvent.click(screen.getByRole('button', { name: 'Or Paste Job Text Directly' }))
    fireEvent.change(screen.getByPlaceholderText('Paste full job description text here...'), { target: { value: '  Backend engineer with Python experience.  ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Analyze Raw Text' }))
    await waitFor(() => expect(analyzeJob).toHaveBeenCalledWith({ url: null, text: 'Backend engineer with Python experience.' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Analyze Raw Text' })).toBeEnabled())
  })

  it('returns to URL submission after closing the error recovery text area', async () => {
    analyzeJob.mockRejectedValueOnce(new Error('Unable to fetch job'))
    analyzeJob.mockResolvedValueOnce({ title: 'Backend Engineer' })
    render(<JobAnalyzer />)
    fireEvent.change(screen.getByPlaceholderText(/Paste LinkedIn/), { target: { value: 'https://example.com/job' } })
    fireEvent.click(screen.getByRole('button', { name: 'Analyze Job', exact: true }))
    fireEvent.click(await screen.findByRole('button', { name: /Switch to Paste Job Text/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Hide Text Area' }))
    fireEvent.click(screen.getByRole('button', { name: 'Analyze Job', exact: true }))
    await waitFor(() => expect(analyzeJob).toHaveBeenCalledTimes(2))
    expect(analyzeJob).toHaveBeenLastCalledWith({ url: 'https://example.com/job', text: null })
    await waitFor(() => expect(screen.getByRole('button', { name: 'Analyze Job', exact: true })).toBeEnabled())
  })
})

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
