import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import ResumeLibrary from '../components/ResumeLibrary'
import * as apiClient from '../api/client'

vi.mock('../api/client', () => ({
  getResumes: vi.fn(),
  prepareResumeProfile: vi.fn(),
  getResumeProfile: vi.fn(),
  reviewResumeProfile: vi.fn(),
  addResume: vi.fn(),
  deleteResume: vi.fn(),
  uploadResumeFile: vi.fn(),
  parseResumeFile: vi.fn(),
  updateResume: vi.fn(),
  downloadResumeFile: vi.fn(),
}))

describe('ResumeLibrary text persistence and upload workflows (B2, B3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiClient.getResumes.mockResolvedValue([])
  })

  it('sends edited content override when saving an uploaded resume', async () => {
    apiClient.parseResumeFile.mockResolvedValue({
      filename: 'sample.pdf',
      suggested_title: 'Sample Resume',
      text: 'Initial extracted text from PDF.',
    })
    apiClient.uploadResumeFile.mockResolvedValue({
      id: 'res-1',
      name: 'Custom Tailored Title',
      content: 'User edited custom bullet points and skills.',
    })

    render(<ResumeLibrary />)

    // Open add resume modal
    await waitFor(() => {
      expect(screen.getByText('Paste Text')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('Paste Text'))

    // Simulate file selection inside modal
    const file = new File(['fake-pdf-content'], 'sample.pdf', { type: 'application/pdf' })
    const fileInputs = document.querySelectorAll('input[type="file"]')
    const modalFileInput = fileInputs[fileInputs.length - 1]
    expect(modalFileInput).not.toBeNull()

    await act(async () => {
      fireEvent.change(modalFileInput, { target: { files: [file] } })
    })

    // Wait for text extraction to populate modal inputs
    await waitFor(() => {
      expect(screen.getByDisplayValue('Initial extracted text from PDF.')).toBeInTheDocument()
    })

    // User edits the title and text content
    const titleInput = screen.getByDisplayValue('Sample Resume')
    const contentTextarea = screen.getByDisplayValue('Initial extracted text from PDF.')

    fireEvent.change(titleInput, { target: { value: 'Custom Tailored Title' } })
    fireEvent.change(contentTextarea, { target: { value: 'User edited custom bullet points and skills.' } })

    // Submit form
    const saveBtn = screen.getByText('Save to Vault')
    await act(async () => {
      fireEvent.click(saveBtn)
    })

    // Verify uploadResumeFile was called with the user's EDITED text override
    expect(apiClient.uploadResumeFile).toHaveBeenCalledWith(
      file,
      'Custom Tailored Title',
      'User edited custom bullet points and skills.'
    )
  })

  it('renders download button labeled Original uploaded file in Quick View', async () => {
    const resume = {
      id: 'resume-123',
      name: 'My Vault Resume',
      content: 'Resume content text.',
      download_url: '/api/resumes/resume-123/download',
      created_at: new Date().toISOString(),
    }
    apiClient.getResumes.mockResolvedValue([resume])

    render(<ResumeLibrary />)

    await waitFor(() => {
      expect(screen.getByText('My Vault Resume')).toBeInTheDocument()
    })

    // Click quick view
    const viewButton = screen.getByTitle('Quick View full resume')
    fireEvent.click(viewButton)

    await waitFor(() => {
      expect(screen.getByText('Original uploaded file')).toBeInTheDocument()
    })
  })
})

describe('Vault profile preparation', () => {
  const resume = { id: 'saved', name: 'Saved Resume', content: 'Saved source text', created_at: '2026-09-30' }
  beforeEach(() => { vi.resetAllMocks(); apiClient.getResumes.mockResolvedValue([resume]); apiClient.prepareResumeProfile.mockResolvedValue({ resume_id: 'saved', status: 'complete', warnings: [] }) })

  it('reads saved review details after reopening without extracting again', async () => {
    apiClient.getResumeProfile.mockResolvedValue({ status: 'needs_review', warnings: ['unresolved_skill_claims'], unresolved_skills: ['inventedtool'] })
    render(<ResumeLibrary profilePreparationEnabled />)
    fireEvent.click(await screen.findByRole('button', { name: 'Check saved analysis for Saved Resume' }))
    expect(await screen.findByText(/Skills needing review: inventedtool/)).toBeInTheDocument()
    expect(apiClient.prepareResumeProfile).not.toHaveBeenCalled()
  })

  it('shows unresolved skills for review without offering a repeated extraction', async () => {
    apiClient.getResumes.mockResolvedValueOnce([]).mockResolvedValue([resume])
    apiClient.uploadResumeFile.mockResolvedValue(resume)
    apiClient.parseResumeFile.mockResolvedValue({ text: resume.content, suggested_title: resume.name })
    apiClient.prepareResumeProfile.mockResolvedValue({ status: 'needs_review', warnings: ['unresolved_skill_claims'], unresolved_skills: ['inventedtool'] })
    render(<ResumeLibrary profilePreparationEnabled />)
    fireEvent.click(await screen.findByText('Paste Text'))
    const inputs = document.querySelectorAll('input[type="file"]')
    fireEvent.change(inputs[inputs.length - 1], { target: { files: [new File(['pdf'], 'saved.pdf', { type: 'application/pdf' })] } })
    await screen.findByDisplayValue(resume.content)
    fireEvent.click(screen.getByText('Save to Vault'))
    expect(await screen.findByText(/Skills needing review: inventedtool/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Retry analysis for Saved Resume' })).not.toBeInTheDocument()
  })

  it('old_resume_profiles_lazily_without_bulk_calls', async () => {
    render(<ResumeLibrary profilePreparationEnabled />)
    await screen.findByText('Saved Resume')
    expect(screen.getByText('Analyzed when compared with a job')).toBeInTheDocument()
    expect(apiClient.prepareResumeProfile).not.toHaveBeenCalled()
  })

  it('profile_analysis_failure_preserves_uploaded_resume', async () => {
    apiClient.getResumes.mockResolvedValueOnce([]).mockResolvedValue([resume])
    apiClient.uploadResumeFile.mockResolvedValue(resume)
    apiClient.parseResumeFile.mockResolvedValue({ text: resume.content, suggested_title: resume.name })
    apiClient.prepareResumeProfile.mockRejectedValueOnce(new Error('Check AI settings and retry.')).mockResolvedValue({ status: 'complete', warnings: [] })
    render(<ResumeLibrary profilePreparationEnabled />)
    fireEvent.click(await screen.findByText('Paste Text'))
    const inputs = document.querySelectorAll('input[type="file"]')
    fireEvent.change(inputs[inputs.length - 1], { target: { files: [new File(['pdf'], 'saved.pdf', { type: 'application/pdf' })] } })
    await screen.findByDisplayValue(resume.content)
    fireEvent.click(screen.getByText('Save to Vault'))
    await screen.findByText(/Analysis failed/)
    expect(screen.getByText('Saved Resume')).toBeInTheDocument()
    expect(screen.queryByText('Save to Vault')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Retry analysis for Saved Resume' }))
    await screen.findByText('Ready for job comparison')
    expect(apiClient.uploadResumeFile).toHaveBeenCalledTimes(1)
    expect(apiClient.prepareResumeProfile).toHaveBeenCalledTimes(2)
  })

  it('repeat_profile_preparation_reuses_saved_analysis_and_rename_skips_preparation', async () => {
    apiClient.updateResume.mockResolvedValue({ ...resume, name: 'Renamed' })
    render(<ResumeLibrary profilePreparationEnabled />)
    await screen.findByText('Saved Resume')
    fireEvent.click(screen.getByTitle('Rename resume title'))
    fireEvent.change(screen.getByDisplayValue('Saved Resume'), { target: { value: 'Renamed' } })
    fireEvent.click(screen.getByTitle('Save title'))
    await screen.findByText('Renamed')
    expect(apiClient.prepareResumeProfile).not.toHaveBeenCalled()
  })

  it('saved_content_edit_prepares_profile_and_publishes_current_resume', async () => {
    const updated = { ...resume, content: 'Edited saved evidence' }, onResumesUpdated = vi.fn()
    apiClient.updateResume.mockResolvedValue(updated)
    render(<ResumeLibrary profilePreparationEnabled onResumesUpdated={onResumesUpdated} />)
    await screen.findByText('Saved Resume')
    fireEvent.click(screen.getByTitle('Quick View full resume'))
    fireEvent.click(screen.getByRole('button', { name: 'Edit saved text' }))
    fireEvent.change(screen.getByLabelText('Saved resume text'), { target: { value: updated.content } })
    fireEvent.click(screen.getByRole('button', { name: 'Save text' }))
    await waitFor(() => expect(apiClient.prepareResumeProfile).toHaveBeenCalledWith('saved', expect.objectContaining({ signal: expect.any(AbortSignal) })))
    expect(apiClient.updateResume).toHaveBeenCalledWith('saved', { content: updated.content })
    expect(onResumesUpdated).toHaveBeenLastCalledWith([updated])
    await screen.findByText('Ready for job comparison')
  })
})

it('preserves_saved_extraction_warnings', async () => {
  apiClient.getResumes.mockResolvedValue([{ id: 'warned', name: 'Warning resume', content: 'Readable page', extraction_warnings: ['PDF page 2 did not contain extractable text.'] }])
  render(<ResumeLibrary profilePreparationEnabled />)
  expect(await screen.findByText('PDF page 2 did not contain extractable text.')).toBeInTheDocument()
})

it('ignores_previous_preparation_response_after_provider_switch', async () => {
  const resume = { id: 'saved', name: 'Saved Resume', content: 'Old text' }
  apiClient.getResumes.mockResolvedValue([resume])
  apiClient.updateResume.mockResolvedValue({ ...resume, content: 'New text' })
  let resolvePrevious
  apiClient.prepareResumeProfile.mockReturnValue(new Promise(resolve => { resolvePrevious = resolve }))
  const { rerender } = render(<ResumeLibrary profilePreparationEnabled refreshKey={0} />)
  await screen.findByText('Saved Resume')
  fireEvent.click(screen.getByTitle('Quick View full resume'))
  fireEvent.click(screen.getByText('Edit saved text'))
  fireEvent.change(screen.getByLabelText('Saved resume text'), { target: { value: 'New text' } })
  fireEvent.click(screen.getByText('Save text'))
  await screen.findByText('Preparing resume analysis...')
  const oldSignal = apiClient.prepareResumeProfile.mock.calls.at(-1)[1].signal
  rerender(<ResumeLibrary profilePreparationEnabled refreshKey={1} />)
  expect(oldSignal.aborted).toBe(true)
  await act(async () => resolvePrevious({ status: 'complete', warnings: [] }))
  expect(screen.queryByText('Ready for job comparison')).not.toBeInTheDocument()
  expect(screen.getByText('Analyzed when compared with a job')).toBeInTheDocument()
})

it('repeated_saved_profile_requests_use_only_current_stored_id', async () => {
  const resume = { id: 'saved', name: 'Saved Resume', content: 'Saved text' }
  apiClient.getResumes.mockResolvedValue([resume])
  apiClient.updateResume.mockResolvedValue(resume)
  apiClient.prepareResumeProfile.mockResolvedValue({ status: 'complete', warnings: [] })
  render(<ResumeLibrary profilePreparationEnabled />)
  await screen.findByText('Saved Resume')
  fireEvent.click(screen.getByTitle('Quick View full resume'))
  for (let i = 0; i < 2; i++) {
    fireEvent.click(screen.getByText('Edit saved text'))
    fireEvent.click(screen.getByText('Save text'))
    await waitFor(() => expect(apiClient.prepareResumeProfile).toHaveBeenCalledTimes(i + 1))
    expect(apiClient.prepareResumeProfile.mock.calls[i]).toEqual(['saved', { signal: expect.any(AbortSignal) }])
    await screen.findByText('Ready for job comparison')
  }
})


it('requires explicit review decisions and saves without preparing again', async () => {
  vi.clearAllMocks()
  apiClient.getResumes.mockResolvedValue([{ id: 'r', name: 'Review me', content: 'Skills: Python' }])
  apiClient.getResumeProfile.mockResolvedValue({ status: 'needs_review', unresolved_skills: ['python', 'invented'], review_token: 'token', warnings: ['unresolved_skill_claims'] })
  apiClient.reviewResumeProfile.mockResolvedValue({ status: 'complete', warnings: [] })
  render(<ResumeLibrary profilePreparationEnabled />)
  fireEvent.click(await screen.findByRole('button', { name: 'Check saved analysis for Review me' }))
  const save = await screen.findByRole('button', { name: 'Save skill review' })
  expect(save).toBeDisabled()
  fireEvent.change(screen.getByLabelText('Decision for python'), { target: { value: 'support' } })
  fireEvent.change(screen.getByLabelText('Supporting text for python'), { target: { value: 'Skills: Python' } })
  fireEvent.change(screen.getByLabelText('Decision for invented'), { target: { value: 'exclude' } })
  fireEvent.click(save)
  await screen.findByText('Ready for job comparison')
  expect(apiClient.reviewResumeProfile).toHaveBeenCalledWith('r', { review_token: 'token', decisions: [{ skill: 'python', source_quote: 'Skills: Python' }, { skill: 'invented', source_quote: null }] }, expect.objectContaining({ signal: expect.any(AbortSignal) }))
  expect(apiClient.prepareResumeProfile).not.toHaveBeenCalled()
})


it('requires full-text confirmation to clear unreadable warnings', async () => {
  const resume = { id: 'warned', name: 'Unreadable', content: 'Complete text', extraction_warnings: ['Missing page'] }
  apiClient.getResumes.mockResolvedValue([resume])
  apiClient.updateResume.mockResolvedValue({ ...resume, extraction_warnings: [] })
  apiClient.prepareResumeProfile.mockResolvedValue({ status: 'complete' })
  render(<ResumeLibrary profilePreparationEnabled />)
  fireEvent.click(await screen.findByTitle('Quick View full resume'))
  fireEvent.click(screen.getByRole('button', { name: 'Edit saved text' }))
  const confirmation = screen.getByRole('checkbox', { name: 'I confirm this is the complete resume text' })
  expect(confirmation).not.toBeChecked()
  fireEvent.click(confirmation)
  fireEvent.click(screen.getByRole('button', { name: 'Save text' }))
  await screen.findByText('Ready for job comparison')
  expect(apiClient.updateResume).toHaveBeenLastCalledWith('warned', { content: 'Complete text', source_reviewed: true })
})
