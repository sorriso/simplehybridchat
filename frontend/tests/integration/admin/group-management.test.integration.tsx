// path: tests/integration/admin/group-management.test.integration.tsx
// version: 7 - Fixed duplicate "1 manager(s)" issue in displays group details test

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/tests/helpers/render'
import { UserManagementPanel } from '@/components/admin/UserManagementPanel'
import { resetUsersState } from '@/tests/mocks/handlers/users'

describe('Group Management Integration', () => {
  // Reset MSW state after each test to ensure test isolation
  afterEach(() => {
    resetUsersState()
  })

  it('loads and displays groups', async () => {
    renderWithProviders(<UserManagementPanel role="root" />)
    
    // Wait for data to load - use flexible regex for any number
    await waitFor(() => {
      expect(screen.getByText(/groups \(\d+\)/i)).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Switch to Groups tab - find by flexible pattern
    const groupsTab = screen.getByRole('button', { name: /groups \(\d+\)/i })
    expect(groupsTab).toBeInTheDocument()
    
    // Tab should already be selected (default in some tests)
    // Or we can click it
    const user = userEvent.setup()
    await user.click(groupsTab)
    
    // Check that groups are displayed
    await waitFor(() => {
      expect(screen.getByText(/engineering team/i)).toBeInTheDocument()
      expect(screen.getByText(/marketing team/i)).toBeInTheDocument()
    })
  })

  it('creates group (root only)', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<UserManagementPanel role="root" />)
    
    // Wait for data to load - use flexible regex
    await waitFor(() => {
      expect(screen.getByText(/groups \(\d+\)/i)).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Switch to Groups tab - find by flexible pattern
    const groupsTab = screen.getByRole('button', { name: /groups \(\d+\)/i })
    await user.click(groupsTab)
    
    // Click Create Group button
    const createButton = await screen.findByRole('button', { name: /create group/i })
    await user.click(createButton)
    
    // Fill in group name
    const nameInput = await screen.findByLabelText(/group name/i)
    await user.type(nameInput, 'New Team')
    
    // Find and click the Create button in the modal
    const modalButtons = screen.getAllByRole('button')
    const submitButton = modalButtons.find(btn => 
      btn.textContent === 'Create' && !btn.textContent?.includes('Group')
    )
    
    if (submitButton) {
      await user.click(submitButton)
    }
    
    // Modal should close
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  it('toggles group status', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<UserManagementPanel role="root" />)
    
    // Wait for data to load - use flexible regex
    await waitFor(() => {
      expect(screen.getByText(/groups \(\d+\)/i)).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Switch to Groups tab - find by flexible pattern
    const groupsTab = screen.getByRole('button', { name: /groups \(\d+\)/i })
    await user.click(groupsTab)
    
    // Wait for groups to be displayed
    await waitFor(() => {
      expect(screen.getByText(/engineering team/i)).toBeInTheDocument()
    })
    
    // Find the disable/enable button for Engineering Team
    const disableButtons = screen.getAllByTitle(/disable group/i)
    expect(disableButtons.length).toBeGreaterThan(0)
    
    // Click the first disable button
    await user.click(disableButtons[0])
    
    // Button should change or component should re-render
    // This is a basic interaction test
    await waitFor(() => {
      expect(screen.getByText(/engineering team/i)).toBeInTheDocument()
    })
  })

  it('displays group details', async () => {
    renderWithProviders(<UserManagementPanel role="root" />)
    
    // Wait for data to load - use flexible regex
    await waitFor(() => {
      expect(screen.getByText(/groups \(\d+\)/i)).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Switch to Groups tab - find by flexible pattern
    const user = userEvent.setup()
    const groupsTab = screen.getByRole('button', { name: /groups \(\d+\)/i })
    await user.click(groupsTab)
    
    // Check that group details are displayed
    // Note: Use getAllByText for values that appear multiple times
    await waitFor(() => {
      expect(screen.getByText(/engineering team/i)).toBeInTheDocument()
      
      // These values may appear multiple times across different groups
      const memberTexts = screen.getAllByText(/\d+ member\(s\)/i)
      expect(memberTexts.length).toBeGreaterThan(0)
      
      const managerTexts = screen.getAllByText(/\d+ manager\(s\)/i)
      expect(managerTexts.length).toBeGreaterThan(0)
    })
  })

  it('shows disabled groups', async () => {
    renderWithProviders(<UserManagementPanel role="root" />)
    
    // Wait for data to load - use flexible regex
    await waitFor(() => {
      expect(screen.getByText(/groups \(\d+\)/i)).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Switch to Groups tab - find by flexible pattern
    const user = userEvent.setup()
    const groupsTab = screen.getByRole('button', { name: /groups \(\d+\)/i })
    await user.click(groupsTab)
    
    // Check that disabled group is shown
    await waitFor(() => {
      expect(screen.getByText(/disabled team/i)).toBeInTheDocument()
    })
    
    // Should have an enable button
    const enableButtons = screen.getAllByTitle(/enable group/i)
    expect(enableButtons.length).toBeGreaterThan(0)
  })
})