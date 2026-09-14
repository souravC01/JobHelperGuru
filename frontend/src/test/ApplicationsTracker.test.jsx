import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
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

  afterEach(() => {
    vi.useRealTimers()
  })

  const followUpApps = [
    ['today', 'Due Today', 'Applied', '2026-09-12'],
    ['overdue', 'Overdue Role', 'Interviewing', '2026-09-11'],
    ['future', 'Future Role', 'Applied', '2026-09-13'],
    ['unset', 'No Follow-Up', 'Applied', null],
    ['rejected', 'Rejected Role', 'Rejected', '2026-09-11'],
    ['archived', 'Archived Role', 'Archived', '2026-09-11'],
    ['offered', 'Offered Role', 'Offered', '2026-09-11'],
  ].map(([id, company, status, follow_up_date]) => ({
    ...sampleApps[0], id, company, status, follow_up_date,
  }))

  it.each(['Table', 'Kanban'])('shows only actionable follow-ups due through the local date in %s view', (view) => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 8, 12, 23, 30))
    render(<ApplicationsTracker applications={followUpApps} />)
    fireEvent.click(screen.getByRole('button', { name: view, exact: true }))
    fireEvent.click(screen.getByRole('button', { name: 'Follow-up due (2)' }))

    expect(screen.getByText('Due Today')).toBeInTheDocument()
    expect(screen.getByText('Overdue Role')).toBeInTheDocument()
    for (const company of ['Future Role', 'No Follow-Up', 'Rejected Role', 'Archived Role', 'Offered Role']) {
      expect(screen.queryByText(company)).not.toBeInTheDocument()
    }
    expect(screen.getByText('2 Roles')).toBeInTheDocument()
  })

  it('combines follow-up filtering with status and search, and restores rows when switched off', () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 8, 12, 23, 30))
    render(<ApplicationsTracker applications={followUpApps} />)
    fireEvent.click(screen.getByRole('button', { name: 'Follow-up due (2)' }))
    fireEvent.click(screen.getByRole('button', { name: 'Applied (3)' }))
    expect(screen.getByText('Due Today')).toBeInTheDocument()
    expect(screen.queryByText('Overdue Role')).not.toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('Search company, role, skills...'), { target: { value: 'Future Role' } })
    expect(screen.queryByText('Due Today')).not.toBeInTheDocument()
    expect(screen.getByText('No applications match your filters.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Follow-up due (2)' }))
    expect(screen.getByText('Future Role')).toBeInTheDocument()
    expect(screen.queryByText('No applications match your filters.')).not.toBeInTheDocument()
  })

  it('renders applications directly from the applications prop', () => {
    render(<ApplicationsTracker applications={sampleApps} onApplicationsChanged={vi.fn()} />)

    expect(screen.getByText('TechCorp')).toBeInTheDocument()
    expect(screen.getByText('Backend Engineer')).toBeInTheDocument()
    expect(screen.getByText('DataFlow')).toBeInTheDocument()
    expect(screen.getByText('Data Engineer')).toBeInTheDocument()
  })

  it.each([
    ['Total Tracked 7', ['Due Today', 'Overdue Role', 'Future Role', 'No Follow-Up', 'Rejected Role', 'Archived Role', 'Offered Role']],
    ['Interviewing 1', ['Overdue Role']],
    ['Offers Received 1', ['Offered Role']],
    ['Follow-ups Set 6', ['Due Today', 'Overdue Role', 'Future Role', 'Rejected Role', 'Archived Role', 'Offered Role']],
  ])('uses the %s card to replace existing filters and search', (card, expectedCompanies) => {
    render(<ApplicationsTracker applications={followUpApps} />)
    fireEvent.click(screen.getByRole('button', { name: /Follow-up due/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Applied (3)' }))
    const search = screen.getByPlaceholderText('Search company, role, skills...')
    fireEvent.change(search, { target: { value: 'nonmatching search' } })

    fireEvent.click(screen.getByRole('button', { name: card, exact: true }))

    expect(search).toHaveValue('')
    for (const app of followUpApps) {
      if (expectedCompanies.includes(app.company)) {
        expect(screen.getByText(app.company)).toBeInTheDocument()
      } else {
        expect(screen.queryByText(app.company)).not.toBeInTheDocument()
      }
    }
    expect(screen.getByRole('button', { name: card, exact: true })).toHaveAttribute('aria-pressed', 'true')
  })

  it('clears the scheduled follow-up filter with Total Tracked while keeping Kanban view', () => {
    render(<ApplicationsTracker applications={followUpApps} />)
    fireEvent.click(screen.getByRole('button', { name: 'Kanban', exact: true }))
    fireEvent.click(screen.getByRole('button', { name: 'Follow-ups Set 6', exact: true }))
    expect(screen.queryByText('No Follow-Up')).not.toBeInTheDocument()
    expect(screen.getByText('Future Role')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Total Tracked 7', exact: true }))
    expect(screen.getByText('No Follow-Up')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.getByText('7 Roles')).toBeInTheDocument()
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
