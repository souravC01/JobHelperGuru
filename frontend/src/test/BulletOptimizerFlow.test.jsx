import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import BulletOptimizerModal from '../components/BulletOptimizerModal'
import * as apiClient from '../api/client'

vi.mock('../api/client', () => ({
  optimizeBullet: vi.fn(),
}))

describe('BulletCraft Resume Optimizer Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockResponse = {
    status: 'rewritten',
    target_keyword: 'Docker',
    target_keywords: ['Docker'],
    claim_status: 'VERIFIED',
    selected_bullet_index: 0,
    target_project_name: 'Cloud Infrastructure',
    original_bullet_to_replace: 'Deployed microservices to servers',
    replacement_rationale: 'Incorporates Docker to highlight containerization skills.',
    alternatives: [
      {
        variant_name: 'Candidate A (ATS-focused)',
        bullet: 'Containerized microservices with Docker to streamline deployments and enhance system scalability.',
        what: 'Docker',
        how: 'Containerized microservices',
        result_or_reason: 'Streamline deployments and enhance scalability',
        claim_status: 'VERIFIED',
        requires_confirmation: false,
      },
    ],
    validation: {
      past_tense: true,
      one_sentence: true,
      one_period_max: true,
      what_how_result_present: true,
      keyword_stuffing: false,
    },
  }

  it('renders BulletCraft branding in the modal header', async () => {
    apiClient.optimizeBullet.mockResolvedValue(mockResponse)

    render(
      <BulletOptimizerModal
        isOpen={true}
        onClose={vi.fn()}
        initialKeywords={['Docker']}
        initialSectionType="work_history"
      />
    )

    expect(screen.getByText('BulletCraft Resume Optimizer')).toBeInTheDocument()
  })

  it('generates recommendations immediately for the selected skill on mount', async () => {
    apiClient.optimizeBullet.mockResolvedValue(mockResponse)

    render(
      <BulletOptimizerModal
        isOpen={true}
        onClose={vi.fn()}
        initialKeywords={['Docker']}
        initialSectionType="work_history"
        targetJobTitle="DevOps Engineer"
      />
    )

    await waitFor(() => {
      expect(apiClient.optimizeBullet).toHaveBeenCalledTimes(1)
    })

    expect(apiClient.optimizeBullet).toHaveBeenCalledWith(
      expect.objectContaining({
        target_keyword: 'Docker',
        target_keywords: ['Docker'],
        section_type: 'work_history',
        target_job_title: 'DevOps Engineer',
      })
    )
  })

  it('passes selected resume content as evidence context to the optimizer', async () => {
    apiClient.optimizeBullet.mockResolvedValue(mockResponse)

    const resume = {
      id: 'res-1',
      name: 'Senior Resume',
      content: 'Experienced engineer with Docker and Kubernetes background.',
    }

    render(
      <BulletOptimizerModal
        isOpen={true}
        onClose={vi.fn()}
        initialKeywords={['Docker']}
        selectedResume={resume}
      />
    )

    await waitFor(() => {
      expect(apiClient.optimizeBullet).toHaveBeenCalledTimes(1)
    })

    expect(apiClient.optimizeBullet).toHaveBeenCalledWith(
      expect.objectContaining({
        evidence_context: [resume.content],
      })
    )
  })

  it('re-generates with project section type when user toggles to Project Bullet', async () => {
    apiClient.optimizeBullet.mockResolvedValue(mockResponse)

    render(
      <BulletOptimizerModal
        isOpen={true}
        onClose={vi.fn()}
        initialKeywords={['PostgreSQL']}
        initialSectionType="work_history"
      />
    )

    await waitFor(() => {
      expect(apiClient.optimizeBullet).toHaveBeenCalledTimes(1)
    })

    const projectTabBtn = screen.getByRole('button', { name: /Project Bullet/i })
    fireEvent.click(projectTabBtn)

    await waitFor(() => {
      expect(apiClient.optimizeBullet).toHaveBeenCalledTimes(2)
    })

    expect(apiClient.optimizeBullet).toHaveBeenLastCalledWith(
      expect.objectContaining({
        target_keywords: ['PostgreSQL'],
        section_type: 'project',
      })
    )
  })

  it('properly targets sequential skills when opening skill A then skill B', async () => {
    apiClient.optimizeBullet.mockResolvedValue(mockResponse)

    // First open for Python
    const { unmount } = render(
      <BulletOptimizerModal
        key="opt-Python-work_history"
        isOpen={true}
        onClose={vi.fn()}
        initialKeywords={['Python']}
      />
    )

    await waitFor(() => {
      expect(apiClient.optimizeBullet).toHaveBeenCalledWith(
        expect.objectContaining({ target_keywords: ['Python'] })
      )
    })

    // Simulate modal close and unmount
    unmount()

    // Second open for Kubernetes
    render(
      <BulletOptimizerModal
        key="opt-Kubernetes-work_history"
        isOpen={true}
        onClose={vi.fn()}
        initialKeywords={['Kubernetes']}
      />
    )

    await waitFor(() => {
      expect(apiClient.optimizeBullet).toHaveBeenLastCalledWith(
        expect.objectContaining({ target_keywords: ['Kubernetes'] })
      )
    })

    expect(apiClient.optimizeBullet).toHaveBeenCalledTimes(2)
  })
})
