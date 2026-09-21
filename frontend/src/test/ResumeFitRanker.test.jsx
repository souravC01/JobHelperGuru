import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import ResumeFitRanker from '../components/ResumeFitRanker'
import * as apiClient from '../api/client'

vi.mock('../api/client', () => ({
  matchResumes: vi.fn(),
  evaluateResumes: vi.fn(),
}))

describe('ResumeFitRanker', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const legacyJob = {
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

  const legacyResumes = [
    { id: 'res-1', name: 'Eligible Candidate', content: 'Python, SQL' },
    { id: 'res-2', name: 'Ineligible Candidate', content: 'Python, SQL' },
    { id: 'res-3', name: 'Unknown Candidate', content: 'Python, SQL' },
  ]

  it('renders distinct badges for eligible, ineligible, and unknown graduation timeline states (legacy fallback)', async () => {
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

    render(<ResumeFitRanker currentJob={legacyJob} resumes={legacyResumes} />)

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

  it('renders v2 competition ranks, tied badges (Rank #1 Tie), and evidence quotes', async () => {
    const job = {
      raw_text: 'Required skills:\nPython\nAWS\n',
      title: 'Senior Backend Engineer',
    }
    const resumes = [
      { id: 'res-1', name: 'Resume Alpha', content: 'Built Python APIs.' },
      { id: 'res-2', name: 'Resume Beta', content: 'Developed Python services.' },
      { id: 'res-3', name: 'Resume Gamma', content: 'Junior developer.' },
    ]

    apiClient.evaluateResumes.mockResolvedValue({
      job_fingerprint: 'job-1',
      comparison_complete: true,
      evaluations: [
        {
          resume_id: 'res-1',
          status: 'complete',
          match_score: 85,
          raw_score: '85.00',
          rank: 1,
          is_top_match: true,
          category_scores: {
            required_skills: { weight: 60, credited_weight: '50.00', coverage_ratio: '0.83' },
          },
          requirement_results: [
            {
              requirement: { id: 'req-1', text: 'Python', category: 'required_skills', source_quote: 'Required: Python' },
              evidence: [{ level: 'demonstrated', source_quote: 'Built Python APIs in production' }],
            },
          ],
        },
        {
          resume_id: 'res-2',
          status: 'complete',
          match_score: 85,
          raw_score: '85.00',
          rank: 1,
          is_top_match: true,
          category_scores: {
            required_skills: { weight: 60, credited_weight: '50.00', coverage_ratio: '0.83' },
          },
          requirement_results: [
            {
              requirement: { id: 'req-1', text: 'Python', category: 'required_skills', source_quote: 'Required: Python' },
              evidence: [{ level: 'demonstrated', source_quote: 'Developed Python services' }],
            },
          ],
        },
        {
          resume_id: 'res-3',
          status: 'complete',
          match_score: 50,
          raw_score: '50.00',
          rank: 3,
          is_top_match: false,
          category_scores: {
            required_skills: { weight: 60, credited_weight: '30.00', coverage_ratio: '0.50' },
          },
          requirement_results: [
            {
              requirement: { id: 'req-1', text: 'Python', category: 'required_skills', source_quote: 'Required: Python' },
              evidence: [{ level: 'listed', source_quote: 'Python' }],
            },
          ],
        },
      ],
    })

    render(<ResumeFitRanker currentJob={job} resumes={resumes} />)

    await waitFor(() => {
      expect(screen.getByText('Resume Alpha')).toBeInTheDocument()
    })

    // Verified tied rank badges (competition rank: 1, 1, 3)
    const tieBadges = screen.getAllByText('Rank #1 Tie')
    expect(tieBadges.length).toBe(2)

    // Verified rank 3 badge
    expect(screen.getByText('#3')).toBeInTheDocument()

    // Verified category breakdown
    expect(screen.getByText('Category Breakdown')).toBeInTheDocument()

    // Verified source quote and candidate evidence quote
    expect(screen.getByText(/Job requirement: “Required: Python”/i)).toBeInTheDocument()
    expect(screen.getByText(/Resume evidence: “Built Python APIs in production”/i)).toBeInTheDocument()
  })

  it('adopted bullet skills remain an edit preview and do not inflate backend match score or rank', async () => {
    const job = { raw_text: 'Required skills: Python', title: 'Python Dev' }
    const resumes = [{ id: 'res-1', name: 'Candidate A', content: 'Python developer' }]
    apiClient.evaluateResumes.mockResolvedValue({
      job_fingerprint: 'job-1',
      comparison_complete: true,
      evaluations: [
        {
          resume_id: 'res-1',
          status: 'complete',
          match_score: 75,
          raw_score: '75.00',
          rank: 1,
          is_top_match: true,
          category_scores: {
            required_skills: { weight: 100, credited_weight: '75.00', coverage_ratio: '0.75' },
          },
          requirement_results: [],
        },
      ],
    })

    render(
      <ResumeFitRanker
        currentJob={job}
        resumes={resumes}
        adoptedSkillsMap={{ 'res-1': ['Kubernetes', 'Docker'] }}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Candidate A')).toBeInTheDocument()
    })

    // Backend score remains strictly 75% without artificial boost
    expect(screen.getByText('75%')).toBeInTheDocument()
    expect(screen.queryByText('85%')).not.toBeInTheDocument()
    expect(screen.queryByText('100%')).not.toBeInTheDocument()

    // Preview badge is rendered
    expect(screen.getByText('+2 in preview')).toBeInTheDocument()
    expect(screen.getByText(/BulletCraft Preview \(2\)/i)).toBeInTheDocument()
  })

  it('renders unranked state for failed or unscorable evaluation without a fabricated score', async () => {
    const job = { raw_text: 'About us: startup with great food', title: 'Unscorable' }
    const resumes = [{ id: 'res-1', name: 'Candidate X', content: 'Engineer' }]
    apiClient.evaluateResumes.mockResolvedValue({
      job_fingerprint: 'job-unscorable',
      comparison_complete: false,
      evaluations: [
        {
          resume_id: 'res-1',
          status: 'needs_review',
          match_score: null,
          rank: null,
          is_top_match: false,
          warnings: ['No evaluable requirements could be extracted.'],
        },
      ],
    })

    render(<ResumeFitRanker currentJob={job} resumes={resumes} />)

    await waitFor(() => {
      expect(screen.getByText('Candidate X')).toBeInTheDocument()
    })

    expect(screen.getByText('Unranked')).toBeInTheDocument()
    expect(screen.getByText('Needs Review')).toBeInTheDocument()
    expect(screen.getByText('Evaluation Incomplete')).toBeInTheDocument()
    expect(screen.getByText(/No evaluable requirements could be extracted/i)).toBeInTheDocument()
    expect(screen.queryByText('%')).not.toBeInTheDocument()
  })

  it('zero match score does not display Top Fit badge', async () => {
    const job = { raw_text: 'Required skills: Python', title: 'Python Dev' }
    const resumes = [{ id: 'res-1', name: 'Candidate Zero', content: 'Ruby only' }]
    apiClient.evaluateResumes.mockResolvedValue({
      job_fingerprint: 'job-1',
      comparison_complete: true,
      evaluations: [
        {
          resume_id: 'res-1',
          status: 'complete',
          match_score: 0,
          raw_score: '0.00',
          rank: 1,
          is_top_match: false,
          category_scores: {
            required_skills: { weight: 100, credited_weight: '0.00', coverage_ratio: '0.00' },
          },
          requirement_results: [],
        },
      ],
    })

    render(<ResumeFitRanker currentJob={job} resumes={resumes} />)

    await waitFor(() => {
      expect(screen.getByText('Candidate Zero')).toBeInTheDocument()
    })

    expect(screen.getByText('0%')).toBeInTheDocument()
    expect(screen.queryByText(/Top Fit/i)).not.toBeInTheDocument()
  })

  it('guards against out-of-order responses from fast job switches', async () => {
    let resolveJobA
    const promiseA = new Promise((resolve) => {
      resolveJobA = resolve
    })
    const promiseB = Promise.resolve({
      job_fingerprint: 'job-b',
      comparison_complete: true,
      evaluations: [
        {
          resume_id: 'res-1',
          status: 'complete',
          match_score: 90,
          rank: 1,
          is_top_match: true,
          category_scores: {},
          requirement_results: [],
        },
      ],
    })

    apiClient.evaluateResumes
      .mockReturnValueOnce(promiseA)
      .mockReturnValueOnce(promiseB)

    const resumes = [{ id: 'res-1', name: 'Fast Switch Candidate', content: 'Skills' }]
    const { rerender } = render(
      <ResumeFitRanker currentJob={{ raw_text: 'Job A text', id: 'job-a' }} resumes={resumes} />
    )

    // Switch to Job B before Job A resolves
    rerender(
      <ResumeFitRanker currentJob={{ raw_text: 'Job B text', id: 'job-b' }} resumes={resumes} />
    )

    await waitFor(() => {
      expect(screen.getByText('90%')).toBeInTheDocument()
    })

    // Now resolve Job A late with score 20%
    resolveJobA({
      job_fingerprint: 'job-a',
      comparison_complete: true,
      evaluations: [
        {
          resume_id: 'res-1',
          status: 'complete',
          match_score: 20,
          rank: 1,
          is_top_match: true,
          category_scores: {},
          requirement_results: [],
        },
      ],
    })

    // Score remains 90% (Job B), ignoring late Job A response
    expect(screen.getByText('90%')).toBeInTheDocument()
    expect(screen.queryByText('20%')).not.toBeInTheDocument()
  })
})
