import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import CoverLetterModal from '../components/CoverLetterModal'
import * as apiClient from '../api/client'

vi.mock('../api/client', () => ({
  generateOutreach: vi.fn(),
  exportCoverLetterDocx: vi.fn(),
}))

describe('CoverLetterModal 3-paragraph format and docx/pdf download', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockJob = {
    title: 'Senior Software Engineer',
    company: 'Stripe',
  }

  const mockResume = {
    id: 'resume-1',
    name: 'Software_Engineer_Resume_2026.pdf',
    content: 'Experienced engineer with Python and distributed systems expertise.',
  }

  const mockUser = {
    id: 'user-1',
    name: 'Sarah Connor',
    email: 'sarah@example.com',
  }

  const mockOutreachData = {
    subject_line: 'Application: Senior Software Engineer - Sarah Connor',
    cover_letter_pitch:
      'Dear Hiring Team at Stripe,\n\n' +
      'I am writing to express my enthusiasm for the Senior Software Engineer position at Stripe.\n\n' +
      'My hands-on experience designing low-latency payment pipelines directly matches Stripe engineering.\n\n' +
      'I look forward to discussing how my experience will help advance your team roadmap.\n\n' +
      'Sincerely,\nSarah Connor',
    connection_note:
      'Hi! I noticed the Senior Software Engineer opening at Stripe and would love to connect.',
  }

  it('renders 3-paragraph cover letter, subject line, and linkedin note with docx and pdf download buttons', async () => {
    apiClient.generateOutreach.mockResolvedValue(mockOutreachData)

    render(
      <CoverLetterModal
        isOpen={true}
        onClose={vi.fn()}
        currentJob={mockJob}
        selectedResume={mockResume}
        currentUser={mockUser}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('3-Paragraph Cover Letter')).toBeInTheDocument()
    })

    // Verify Subject Line and LinkedIn note sections
    expect(screen.getByText('Suggested Email Subject Line')).toBeInTheDocument()
    expect(screen.getByText(mockOutreachData.subject_line)).toBeInTheDocument()
    expect(screen.getByText(/LinkedIn \/ Recruiter InMail Note/i)).toBeInTheDocument()
    expect(screen.getByText(mockOutreachData.connection_note)).toBeInTheDocument()

    // Verify only .docx and .pdf download buttons exist (no .txt or .md)
    expect(screen.getByRole('button', { name: /Download Word \(\.docx\)/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download PDF/i })).toBeInTheDocument()
    expect(screen.queryByText(/Download Text/i)).toBeNull()
    expect(screen.queryByText(/Download Markdown/i)).toBeNull()
    expect(screen.queryByText(/\.txt/i)).toBeNull()
    expect(screen.queryByText(/\.md/i)).toBeNull()
  })

  it('prefers candidate name from account info instead of resume name for outreach and export', async () => {
    apiClient.generateOutreach.mockResolvedValue(mockOutreachData)
    apiClient.exportCoverLetterDocx.mockResolvedValue()

    render(
      <CoverLetterModal
        isOpen={true}
        onClose={vi.fn()}
        currentJob={mockJob}
        selectedResume={mockResume}
        currentUser={mockUser}
      />
    )

    await waitFor(() => {
      expect(apiClient.generateOutreach).toHaveBeenCalledWith({
        job: mockJob,
        resume_id: mockResume.id,
        resume_content: mockResume.content,
        candidate_name: 'Sarah Connor',
      })
    })

    const docxBtn = screen.getByRole('button', { name: /Download Word \(\.docx\)/i })
    await act(async () => {
      fireEvent.click(docxBtn)
    })

    expect(apiClient.exportCoverLetterDocx).toHaveBeenCalledWith({
      cover_letter_text: mockOutreachData.cover_letter_pitch,
      candidate_name: 'Sarah Connor',
      company: 'Stripe',
      role: 'Senior Software Engineer',
      subject_line: mockOutreachData.subject_line,
    })
  })
})
