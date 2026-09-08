import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import ResumeLibrary from '../components/ResumeLibrary'
import * as apiClient from '../api/client'

vi.mock('../api/client', () => ({
  getResumes: vi.fn(),
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
