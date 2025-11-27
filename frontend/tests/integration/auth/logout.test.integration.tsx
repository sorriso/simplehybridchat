// path: tests/integration/auth/logout.test.integration.tsx
// version: 8

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/tests/helpers/render'
import { SettingsPanel } from '@/components/settings/SettingsPanel'
import { storage } from '@/lib/utils/storage'

describe('Logout Integration', () => {
  beforeEach(() => {
    // Set initial auth token
    storage.setAuthToken('test-token')
  })

  afterEach(() => {
    storage.clearAuthToken()
  })

  it('clears localStorage on logout', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<SettingsPanel />)
    
    // Verify token exists before logout
    expect(storage.getAuthToken()).toBe('test-token')
    
    // Find the specific "Logout" button
    const logoutButton = screen.getByRole('button', { name: /^logout$/i })
    await user.click(logoutButton)
    
    await waitFor(() => {
      expect(storage.getAuthToken()).toBeNull()
    })
  })
})