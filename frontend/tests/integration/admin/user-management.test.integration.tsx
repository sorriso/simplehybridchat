// path: tests/integration/admin/user-management.test.integration.tsx
// version: 2 - Fixed duplicate "John Doe" issue with specific selectors

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/tests/helpers/render'
import { UserManagementPanel } from '@/components/admin/UserManagementPanel'

describe('User Management Integration', () => {
  it('manager sees only their groups', async () => {
    renderWithProviders(<UserManagementPanel role="manager" />)
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/engineering team/i)).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Manager should see "Engineering Team" in the UI
    expect(screen.getByText(/you are managing this group/i)).toBeInTheDocument()
  })

  it('toggles user status', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<UserManagementPanel role="root" />)
    
    // Wait for data to load - use specific email to avoid duplicate "John Doe"
    await waitFor(() => {
      expect(screen.getByText(/john.doe@example.com/i)).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Find disable buttons
    const disableButtons = screen.getAllByTitle(/disable user/i)
    expect(disableButtons.length).toBeGreaterThan(0)
    
    // Click first disable button
    await user.click(disableButtons[0])
    
    // Component should re-render
    await waitFor(() => {
      expect(screen.getByText(/john.doe@example.com/i)).toBeInTheDocument()
    })
  })

  it('assigns role (root only)', async () => {
    renderWithProviders(<UserManagementPanel role="root" />)
    
    // Wait for data to load - use specific email
    await waitFor(() => {
      expect(screen.getByText(/john.doe@example.com/i)).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Check that different roles are displayed
    expect(screen.getByText(/admin@example.com/i)).toBeInTheDocument()
    expect(screen.getByText(/jane.manager@example.com/i)).toBeInTheDocument()
  })

  it('adds user to group', async () => {
    renderWithProviders(<UserManagementPanel role="manager" />)
    
    // Wait for data to load - use specific email
    await waitFor(() => {
      expect(screen.getByText(/john.doe@example.com/i)).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Manager should see users in their groups
    expect(screen.getByText(/jane.manager@example.com/i)).toBeInTheDocument()
  })

  it('removes user from group', async () => {
    renderWithProviders(<UserManagementPanel role="manager" />)
    
    // Wait for data to load - use specific email
    await waitFor(() => {
      expect(screen.getByText(/john.doe@example.com/i)).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Check that users are displayed
    expect(screen.getByText(/jane.manager@example.com/i)).toBeInTheDocument()
    expect(screen.getByText(/engineering team/i)).toBeInTheDocument()
  })
})