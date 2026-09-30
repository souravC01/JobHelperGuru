import { render, screen, fireEvent } from '@testing-library/react'
import { it, expect, vi } from 'vitest'
import App from '../App'
import { setAuth } from '../api/client'

vi.mock('../components/JobAnalyzer', () => ({ default: ({ onJobAnalyzed, onOpenBulletOptimizer }) => <><button onClick={() => onJobAnalyzed({ raw_text: 'Full job' })}>Analyze fixture</button><button onClick={() => onOpenBulletOptimizer(['Python'])}>Craft fixture</button></> }))
vi.mock('../components/ResumeFitRanker', () => ({ default: ({ onBestResumeSelected, matchingEnabled }) => <><span>{matchingEnabled ? 'Matching enabled' : 'Matching pending'}</span><button onClick={() => onBestResumeSelected(null)}>Clear selection</button><button onClick={() => onBestResumeSelected({ resume_id: 'r' })}>Select compatible result</button><button onClick={() => onBestResumeSelected({ id: 'r' })}>Select stored resume</button></> }))
vi.mock('../components/BulletOptimizerModal', () => ({ default: ({ selectedResume }) => <span>Optimizer: {selectedResume?.content || 'none'}</span> }))
vi.mock('../components/CoverLetterModal', () => ({ default: ({ selectedResume }) => <span>Selected: {selectedResume?.content || 'none'}</span> }))

it('nullable_best_resume_callback_is_safe_and_resolves_stored_resume', async () => {
  const user = { id: 'user', name: 'User' }, resume = { id: 'r', name: 'Resume', content: 'Stored source' }
  setAuth('token', user)
  fetch.mockImplementation(async url => ({ ok: true, status: 200, json: async () => String(url).includes('/auth/me') ? user : String(url).includes('/resumes') ? [resume] : String(url).includes('/features') ? { matching_v2_enabled: true } : String(url).includes('/settings') ? { has_api_key: true, use_offline_mode: false } : [] }))
  render(<App />)
  await screen.findByText('Selected: Stored source')
  fireEvent.click(screen.getByText('Analyze fixture'))
  fireEvent.click(screen.getByText('Clear selection'))
  await screen.findByText('Selected: none')
  await screen.findByText('Matching enabled')
  const alert = vi.spyOn(window, 'alert').mockImplementation(() => {})
  fireEvent.click(screen.getByText('Craft fixture'))
  expect(screen.queryByText('Optimizer: Stored source')).not.toBeInTheDocument()
  expect(alert).toHaveBeenCalledWith(expect.stringMatching(/Choose a resume/))
  alert.mockRestore()
  for (const label of ['Select compatible result', 'Select stored resume']) {
    fireEvent.click(screen.getByText(label))
    await screen.findByText('Selected: Stored source')
    fireEvent.click(screen.getByText('Clear selection'))
    await screen.findByText('Selected: none')
  }
})
