import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import ResumeFitRanker from '../components/ResumeFitRanker'
import * as apiClient from '../api/client'

vi.mock('../api/client', () => ({
  matchResumes: vi.fn(),
}))

describe('ResumeFitRanker 3-state graduation timeline UI (B14)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const job = {
    analysis: {
      company: 'TestCorp',
      title: 'Graduate Software Engineer',
      is_new_grad_role: true,
      new_grad_criteria: 'Between May 2025 and June 2026',
      required_skills: ['Python', 'SQL'],
      tech_stack: ['Python', 'SQL'],
      ats_keywords: ['Python'],
    },
  }

  const resumes = [
    { id: 'res-1', name: 'Eligible Candidate', content: 'Python, SQL' },
    { id: 'res-2', name: 'Ineligible Candidate', content: 'Python, SQL' },
    { id: 'res-3', name: 'Unknown Candidate', content: 'Python, SQL' },
  ]

  it('renders distinct badges for eligible, ineligible, and unknown graduation timeline states', async () => {
    apiClient.matchResumes.mockResolvedValue([
      {
        resume_id: 'res-1',
        resume_name: 'Eligible Candidate',
        match_score: 95,
        matched_keywords: ['Python', 'SQL'],
        missing_keywords: [],
        fit_summary: 'Excellent alignment.',
        is_new_grad_role: true,
        new_grad_eligible: true,
        graduation_status: 'Graduating in 2 months (May 2026)',
        graduation_date: 'May 2026',
      },
      {
        resume_id: 'res-2',
        resume_name: 'Ineligible Candidate',
        match_score: 80,
        matched_keywords: ['Python'],
        missing_keywords: ['SQL'],
        fit_summary: 'Good match.',
        is_new_grad_role: true,
        new_grad_eligible: false,
        graduation_status: 'Graduated 3 years ago (May 2023)',
        graduation_date: 'May 2023',
      },
      {
        resume_id: 'res-3',
        resume_name: 'Unknown Candidate',
        match_score: 75,
        matched_keywords: ['Python'],
        missing_keywords: ['SQL'],
        fit_summary: 'Fair match.',
        is_new_grad_role: true,
        new_grad_eligible: null,
        graduation_status: 'Graduation date not detected',
        graduation_date: null,
      },
    ])

    render(<ResumeFitRanker currentJob={job} resumes={resumes} />)

    await waitFor(() => {
      expect(screen.getByText('Eligible Candidate')).toBeInTheDocument()
    })

    // State 1: Eligible
    expect(screen.getByText(/New Grad Eligible \(Graduating in 2 months/i)).toBeInTheDocument()
    expect(screen.getByText('Meets Timeline')).toBeInTheDocument()

    // State 2: Ineligible
    expect(screen.getByText(/Timeline Ineligible \(Graduated 3 years ago/i)).toBeInTheDocument()

    // State 3: Unknown
    expect(screen.getByText(/Timeline Unknown \(Graduation date not detected\)/i)).toBeInTheDocument()
  })
})
