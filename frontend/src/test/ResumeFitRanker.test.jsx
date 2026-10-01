import { render, screen, waitFor, act, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import ResumeFitRanker from '../components/ResumeFitRanker'
import * as apiClient from '../api/client'

vi.mock('../api/client', () => ({
  matchResumes: vi.fn(),
  evaluateResumes: vi.fn(),
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

const stored = [{ id: 'a', name: 'Resume A', content: 'Built Python services' }, { id: 'b', name: 'Resume B', content: 'SQL reporting' }]
const fullJob = { id: 'job-a', raw_text: 'Build Python services and SQL reporting' }
const result = (id, score = 80, rank = 1) => ({ resume_id: id, status: 'complete', match_score: score, raw_score: String(score), rank, is_top_match: rank === 1 && score > 0, category_scores: { required_skills: '75.50' }, skill_coverage_score: '50.00', warnings: [] })
const batch = (evaluations = [result('a'), result('b', 50, 2)], comparison_complete = true) => ({ comparison_complete, evaluations })
const deferred = () => { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no }); return { promise, resolve, reject } }
const props = { currentJob: fullJob, resumes: stored, matchingEnabled: true, aiProviderReady: true }

describe('Skill fit UI and lifecycle', () => {
  beforeEach(() => { vi.resetAllMocks(); apiClient.evaluateResumes.mockResolvedValue(batch()) })

  it('reranks_after_same_count_content_edit', async () => {
    const { rerender } = render(<ResumeFitRanker {...props} />)
    await screen.findByText('80%')
    rerender(<ResumeFitRanker {...props} resumes={[{ ...stored[0], content: 'Edited experience' }, stored[1]]} />)
    await waitFor(() => expect(apiClient.evaluateResumes).toHaveBeenCalledTimes(2))
    expect(apiClient.evaluateResumes).toHaveBeenLastCalledWith(fullJob.raw_text, ['a', 'b'], expect.objectContaining({ fresh: false, signal: expect.any(AbortSignal) }))
  })

  for (const change of ['job', 'profile']) {
    it(`ignores_previous_${change}_response`, async () => {
      const previous = deferred(), current = deferred()
      const selected = vi.fn()
      apiClient.evaluateResumes.mockReturnValueOnce(previous.promise).mockReturnValueOnce(current.promise)
      const { rerender } = render(<ResumeFitRanker {...props} onBestResumeSelected={selected} />)
      const oldSignal = apiClient.evaluateResumes.mock.calls[0][2].signal
      rerender(<ResumeFitRanker {...props} currentJob={change === 'job' ? { raw_text: 'New job' } : fullJob} refreshKey={change === 'profile' ? 1 : 0} onBestResumeSelected={selected} />)
      expect(oldSignal.aborted).toBe(true)
      await act(async () => previous.resolve(batch([result('a', 99)])))
      expect(screen.queryByText('99%')).not.toBeInTheDocument()
      expect(screen.getByRole('status')).toHaveTextContent('Evaluating')
      await act(async () => current.resolve(batch([result('b', 65)])))
      expect(screen.getByText('65%')).toBeInTheDocument()
      expect(selected).toHaveBeenLastCalledWith(stored[1])
    })
  }

  it('ties_show_equal_rank_without_auto_choice', async () => {
    apiClient.evaluateResumes.mockResolvedValue(batch([result('a'), result('b')]))
    const selected = vi.fn()
    render(<ResumeFitRanker {...props} onBestResumeSelected={selected} />)
    await screen.findByText(/Tied leaders/)
    expect(screen.getAllByText('Rank 1')).toHaveLength(2)
    expect(selected).not.toHaveBeenCalledWith(expect.objectContaining({ id: 'a' }))
    expect(selected).toHaveBeenLastCalledWith(null)
    fireEvent.click(screen.getByRole('button', { name: 'Use Resume B' }))
    expect(selected).toHaveBeenLastCalledWith(stored[1])
  })

  it('incomplete_batch_has_no_top_badge', async () => {
    apiClient.evaluateResumes.mockResolvedValue(batch([result('a'), { resume_id: 'b', status: 'needs_review', reason_codes: ['source_incomplete'], warnings: ['Resume text is incomplete.'] }], false))
    const selected = vi.fn()
    render(<ResumeFitRanker {...props} onBestResumeSelected={selected} />)
    await screen.findByText(/Comparison incomplete/)
    expect(screen.queryByText('Top Fit')).not.toBeInTheDocument()
    expect(screen.queryByText('Rank 1')).not.toBeInTheDocument()
    expect(screen.getByText(/Resume text is incomplete/)).toBeInTheDocument()
    expect(screen.getByText('Needs review')).toBeInTheDocument()
    expect(selected).toHaveBeenLastCalledWith(null)
  })

  it('adopted_keyword_does_not_raise_backend_score', async () => {
    const { rerender } = render(<ResumeFitRanker {...props} />)
    await screen.findByText('80%')
    rerender(<ResumeFitRanker {...props} adoptedSkillsMap={{ a: ['SQL'] }} />)
    expect(screen.getByText('80%')).toBeInTheDocument()
    expect(screen.getByText('Raw score: 80 / 100')).toBeInTheDocument()
    expect(screen.getAllByText('Required skills: 75.50%')).toHaveLength(2)
    expect(screen.getAllByText('Skill coverage: 50.00%')).toHaveLength(2)
    expect(screen.queryByText(/Boost/)).not.toBeInTheDocument()
    expect(apiClient.evaluateResumes).toHaveBeenCalledTimes(1)
    expect(screen.getByText('Skill fit')).toBeInTheDocument()
  })

  it('shows_required_and_preferred_matched_and_missing_skills', async () => {
    const evaluation = result('a')
    evaluation.score_scope = 'skill_fit'
    evaluation.requirement_results = [
      { requirement: { id: 'python', kind: 'skill', category: 'required_skills', alternatives: ['Python'] }, evidence: [{ level: 'listed' }] },
      { requirement: { id: 'java', kind: 'skill', category: 'required_skills', alternatives: ['Java', 'Rust'] }, evidence: [{ level: 'not_evidenced' }] },
      { requirement: { id: 'sql', kind: 'skill', category: 'preferred_qualifications', alternatives: ['SQL'] }, evidence: [{ level: 'demonstrated' }] },
      { requirement: { id: 'aws', kind: 'skill', category: 'preferred_qualifications', alternatives: ['AWS'] }, evidence: [{ level: 'not_evidenced' }] },
    ]
    apiClient.evaluateResumes.mockResolvedValue(batch([evaluation]))
    render(<ResumeFitRanker {...props} />)
    await screen.findByRole('region', { name: 'Resume skill fit' })
    await screen.findByText('Matched required skills: Python')
    expect(screen.getByText('Missing required skills: Java or Rust')).toBeInTheDocument()
    expect(screen.getByText('Matched preferred skills: SQL')).toBeInTheDocument()
    expect(screen.getByText('Missing preferred skills: AWS')).toBeInTheDocument()
    expect(screen.queryByText(/Responsibilities:/)).not.toBeInTheDocument()
  })

  it('missing_raw_text_requests_full_jd', async () => {
    render(<ResumeFitRanker {...props} currentJob={{ analysis: { title: 'Old job', required_skills: ['Python'] } }} />)
    expect(screen.getByText(/Paste the full job description/)).toBeInTheDocument()
    expect(apiClient.evaluateResumes).not.toHaveBeenCalled()
    fireEvent.change(screen.getByLabelText('Full job description'), { target: { value: 'Original full job description' } })
    fireEvent.click(screen.getByRole('button', { name: 'Evaluate full description' }))
    await screen.findByText('80%')
    expect(apiClient.evaluateResumes.mock.calls[0][0]).toBe('Original full job description')
  })

  it('failed_provider_clears_scores_and_never_switches_offline', async () => {
    const onAiError = vi.fn()
    render(<ResumeFitRanker {...props} onAiError={onAiError} />)
    await screen.findByText('80%')
    apiClient.evaluateResumes.mockRejectedValue(Object.assign(new Error('Check AI settings and retry.'), { status: 502 }))
    fireEvent.click(screen.getByRole('button', { name: 'Re-evaluate' }))
    await screen.findByRole('alert')
    expect(screen.queryByText('80%')).not.toBeInTheDocument()
    expect(onAiError).not.toHaveBeenCalled()
    expect(apiClient.matchResumes).not.toHaveBeenCalled()
    expect(apiClient.evaluateResumes.mock.calls[1][2].fresh).toBe(true)
  })

  it('offline_provider_and_pending_features_never_enter_overall_evaluation', () => {
    const { rerender } = render(<ResumeFitRanker {...props} aiProviderReady={false} />)
    expect(screen.getByText(/Configure an AI provider/)).toBeInTheDocument()
    rerender(<ResumeFitRanker {...props} matchingEnabled={null} />)
    expect(apiClient.evaluateResumes).not.toHaveBeenCalled()
    expect(apiClient.matchResumes).not.toHaveBeenCalled()
  })
})

it('source_less_job_can_explicitly_use_labeled_legacy_alignment', async () => {
  apiClient.matchResumes.mockResolvedValue([{ resume_id: 'a', resume_name: 'Resume A', match_score: 30, matched_keywords: [], missing_keywords: ['Python'] }])
  render(<ResumeFitRanker {...props} currentJob={{ analysis: { required_skills: ['Python'] } }} />)
  fireEvent.click(screen.getByRole('button', { name: 'Use legacy keyword alignment' }))
  await screen.findByText('Legacy keyword alignment')
  expect(apiClient.evaluateResumes).not.toHaveBeenCalled()
  expect(apiClient.matchResumes).toHaveBeenCalledTimes(1)
})
