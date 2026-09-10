import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import SettingsModal from '../components/SettingsModal'
import * as client from '../api/client'

vi.mock('../api/client', () => ({
  getSettings: vi.fn(),
  updateSettings: vi.fn(),
  testAISettings: vi.fn(),
  getProviderProfiles: vi.fn(),
  createProviderProfile: vi.fn(),
  updateProviderProfile: vi.fn(),
  activateProviderProfile: vi.fn(),
  deleteProviderProfile: vi.fn(),
}))

describe('SettingsModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('initializes input fields as empty for a new account without active profile', async () => {
    client.getSettings.mockResolvedValue({
      api_base_url: '',
      api_key: '',
      model_name: '',
      use_offline_mode: false,
      active_profile_id: null,
    })
    client.getProviderProfiles.mockResolvedValue([])

    render(
      <SettingsModal
        isOpen={true}
        onClose={vi.fn()}
        currentUser={{ id: 'user-new', email: 'newuser@example.com' }}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/Configure New Key/i)).toBeInTheDocument()
    })

    const baseUrlInput = screen.getByPlaceholderText(/https:\/\/generativelanguage\.googleapis\.com/i)
    const modelNameInput = screen.getByPlaceholderText(/gemini-2\.0-flash/i)

    expect(baseUrlInput).toHaveValue('')
    expect(modelNameInput).toHaveValue('')
  })
})
