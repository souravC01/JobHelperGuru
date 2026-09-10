import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import ApplicationsTracker from '../components/ApplicationsTracker'
import * as apiClient from '../api/client'
import { localDate } from '../utils/localDate'

vi.mock('../api/client', () => ({
  updateApplication: vi.fn(),
  deleteApplication: vi.fn(),
  downloadExcelReport: vi.fn(),
}))

describe('ApplicationsTracker state synchronization and local dates (B12, B13, B15)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    window.confirm = vi.fn(() => true)
  })

  const sampleApps = [
    {
      id: 'app-1',
      company: 'TechCorp',
      role: 'Backend Engineer',
      status: 'Wishlist',
      date_added: '2026-09-01',
      application_date: null,
      follow_up_date: null,
      notes: 'Initial notes',
      location: 'Remote',
      salary: '$140k',
      required_skills: ['Python', 'FastAPI'],
    },
    {
      id: 'app-2',
      company: 'DataFlow',
      role: 'Data Engineer',
      status: 'Archived',
      date_added: '2026-09-02',
      application_date: '2026-09-02',
      follow_up_date: null,
      notes: '',
      location: 'New York, NY',
      salary: '$160k',
      required_skills: ['SQL', 'Spark'],
    },
  ]

  it('renders applications directly from the applications prop', () => {
    render(<ApplicationsTracker applications={sampleApps} onApplicationsChanged={vi.fn()} />)

    expect(screen.getByText('TechCorp')).toBeInTheDocument()
    expect(screen.getByText('Backend Engineer')).toBeInTheDocument()
    expect(screen.getByText('DataFlow')).toBeInTheDocument()
    expect(screen.getByText('Data Engineer')).toBeInTheDocument()
  })

  it('transitions to Applied with localDate and updates parent via onApplicationsChanged', async () => {
    const onApplicationsChanged = vi.fn()
    const today = localDate()

    const updatedApp = {
      ...sampleApps[0],
      status: 'Applied',
      application_date: today,
      follow_up_date: '2026-09-15',
    }

    apiClient.updateApplication.mockResolvedValueOnce(updatedApp)

    render(<ApplicationsTracker applications={sampleApps} onApplicationsChanged={onApplicationsChanged} />)

    const select = screen.getAllByRole('combobox')[0]
    fireEvent.change(select, { target: { value: 'Applied' } })

    await waitFor(() => {
      expect(apiClient.updateApplication).toHaveBeenCalledWith('app-1', {
        status: 'Applied',
        application_date: today,
      })
    })

    expect(onApplicationsChanged).toHaveBeenCalledTimes(1)
    const updatedList = onApplicationsChanged.mock.calls[0][0]
    expect(updatedList[0].status).toBe('Applied')
    expect(updatedList[0].application_date).toBe(today)
    expect(updatedList[0].follow_up_date).toBe('2026-09-15')
  })

  it('deletes application and propagates updated array to parent', async () => {
    const onApplicationsChanged = vi.fn()
    apiClient.deleteApplication.mockResolvedValueOnce({ success: true })

    render(<ApplicationsTracker applications={sampleApps} onApplicationsChanged={onApplicationsChanged} />)

    const deleteButtons = screen.getAllByTitle('Delete application')
    fireEvent.click(deleteButtons[0])

    await waitFor(() => {
      expect(apiClient.deleteApplication).toHaveBeenCalledWith('app-1')
    })

    expect(onApplicationsChanged).toHaveBeenCalledTimes(1)
    const remaining = onApplicationsChanged.mock.calls[0][0]
    expect(remaining.length).toBe(1)
    expect(remaining[0].id).toBe('app-2')
  })

  it('renders Kanban board with Archived column containing archived application (B15)', () => {
    render(<ApplicationsTracker applications={sampleApps} onApplicationsChanged={vi.fn()} />)

    const kanbanButton = screen.getByRole('button', { name: /kanban/i })
    fireEvent.click(kanbanButton)

    expect(screen.getByText('Archived')).toBeInTheDocument()
    expect(screen.getByText('DataFlow')).toBeInTheDocument()
  })
})
