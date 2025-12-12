// path: frontend/tests/integration/admin/group-management.test.integration.tsx
// version: 18

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/tests/helpers/render'
import { UserManagementPanel } from '@/components/admin/UserManagementPanel'
import { resetUsersState } from '@/tests/mocks/handlers/users'
import type { User } from '@/types/auth'

// Helper to create mock user based on role
const createMockUser = (role: 'root' | 'manager' | 'user'): User => {
  const users = {
    root: {
      id: 'user-root',
      name: 'Admin Root',
      email: 'admin@example.com',
      role: 'root' as const,
      status: 'active' as const,
      groupIds: [],
    },
    manager: {
      id: 'user-manager',
      name: 'Jane Manager',
      email: 'jane.manager@example.com',
      role: 'manager' as const,
      status: 'active' as const,
      groupIds: ['ugroup-1'],
    },
    user: {
      id: 'user-john-doe',
      name: 'John Doe',
      email: 'john.doe@example.com',
      role: 'user' as const,
      status: 'active' as const,
      groupIds: ['ugroup-1'],
    },
  }
  return users[role]
}

// Helper to create permissions based on role
const createPermissions = (role: 'root' | 'manager' | 'user') => {
  return {
    canManageAllUsers: role === 'root',
    canActivateDeactivateGroupMembers: role === 'root' || role === 'manager',
    canManageGroups: role === 'root' || role === 'manager',
    canCreateGroups: role === 'root',
  }
}

describe('Group Management Integration', () => {
  // Reset MSW state after each test to ensure test isolation
  afterEach(() => {
    resetUsersState()
  })

  it('loads and displays groups tab', async () => {
    const currentUser = createMockUser('root')
    const permissions = createPermissions('root')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for tabs to appear
    await waitFor(() => {
      expect(screen.getByText(/users \(/i)).toBeInTheDocument()
    })
    
    // Verify groups tab exists
    expect(screen.getByText(/groups \(/i)).toBeInTheDocument()
  })

  it('switches to groups tab', async () => {
    const user = userEvent.setup()
    const currentUser = createMockUser('root')
    const permissions = createPermissions('root')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for tabs to appear
    await waitFor(() => {
      expect(screen.getByText(/groups \(/i)).toBeInTheDocument()
    })
    
    // Click on Groups tab
    const groupsTab = screen.getByRole('button', { name: /groups \(/i })
    await user.click(groupsTab)
    
    // Verify tab switched - either groups display or "No groups yet"
    await waitFor(() => {
      const noGroups = screen.queryByText(/no groups yet/i)
      const createGroupBtn = screen.queryByRole('button', { name: /create group/i })
      expect(noGroups || createGroupBtn).toBeTruthy()
    })
  })

  it('shows create group button for root user', async () => {
    const user = userEvent.setup()
    const currentUser = createMockUser('root')
    const permissions = createPermissions('root')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for tabs and switch to groups
    await waitFor(() => {
      expect(screen.getByText(/groups \(/i)).toBeInTheDocument()
    })
    
    const groupsTab = screen.getByRole('button', { name: /groups \(/i })
    await user.click(groupsTab)
    
    // Wait for Create Group button
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /create group/i })).toBeInTheDocument()
    })
  })

  it('hides create group button for manager user', async () => {
    const user = userEvent.setup()
    const currentUser = createMockUser('manager')
    const permissions = createPermissions('manager')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for tabs and switch to groups
    await waitFor(() => {
      expect(screen.getByText(/groups \(/i)).toBeInTheDocument()
    })
    
    const groupsTab = screen.getByRole('button', { name: /groups \(/i })
    await user.click(groupsTab)
    
    // Wait for content to load - check for "No groups yet" message
    await waitFor(() => {
      expect(screen.getByText(/no groups yet/i)).toBeInTheDocument()
    })
    
    // Verify Create Group button does not exist
    expect(screen.queryByRole('button', { name: /create group/i })).not.toBeInTheDocument()
  })

  it('displays groups tab counter', async () => {
    const currentUser = createMockUser('root')
    const permissions = createPermissions('root')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for tabs and verify groups counter
    await waitFor(() => {
      expect(screen.getByText(/groups \(\d+\)/i)).toBeInTheDocument()
    })
  })

  it('manager sees groups tab', async () => {
    const currentUser = createMockUser('manager')
    const permissions = createPermissions('manager')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for tabs
    await waitFor(() => {
      expect(screen.getByText(/users \(/i)).toBeInTheDocument()
    })
    
    // Manager should see groups tab
    expect(screen.getByText(/groups \(/i)).toBeInTheDocument()
  })
})