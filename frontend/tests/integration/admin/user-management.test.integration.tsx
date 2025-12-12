// path: frontend/tests/integration/admin/user-management.test.integration.tsx
// version: 11

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/tests/helpers/render'
import { UserManagementPanel } from '@/components/admin/UserManagementPanel'
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

describe('User Management Integration', () => {
  it('loads and displays users tab', async () => {
    const currentUser = createMockUser('root')
    const permissions = createPermissions('root')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for users tab to appear with count
    await waitFor(() => {
      expect(screen.getByText(/users \(/i)).toBeInTheDocument()
    })
  })

  it('displays user list with emails', async () => {
    const currentUser = createMockUser('root')
    const permissions = createPermissions('root')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for user data to load and display
    await waitFor(() => {
      expect(screen.getByText(/john.doe@example.com/i)).toBeInTheDocument()
    })
    
    // Verify other users are also displayed
    expect(screen.getByText(/admin@example.com/i)).toBeInTheDocument()
  })

  it('displays user action buttons', async () => {
    const currentUser = createMockUser('root')
    const permissions = createPermissions('root')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText(/john.doe@example.com/i)).toBeInTheDocument()
    })
    
    // Check for disable/enable buttons - use getAllByTitle
    await waitFor(() => {
      const disableButtons = screen.getAllByTitle(/disable user/i)
      const enableButtons = screen.getAllByTitle(/enable user/i)
      const totalButtons = disableButtons.length + enableButtons.length
      expect(totalButtons).toBeGreaterThan(0)
    })
  })

  it('manager sees only users in their groups', async () => {
    const currentUser = createMockUser('manager')
    const permissions = createPermissions('manager')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for users tab
    await waitFor(() => {
      expect(screen.getByText(/users \(/i)).toBeInTheDocument()
    })
    
    // Manager should see users in their groups
    await waitFor(() => {
      expect(screen.getByText(/john.doe@example.com/i)).toBeInTheDocument()
    })
    
    // Manager should see themselves
    expect(screen.getByText(/jane.manager@example.com/i)).toBeInTheDocument()
  })

  it('root sees all users indicator', async () => {
    const currentUser = createMockUser('root')
    const permissions = createPermissions('root')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByText(/users \(/i)).toBeInTheDocument()
    })
    
    // Root should see "All Users" indicator
    expect(screen.getByText(/all users/i)).toBeInTheDocument()
  })

  it('displays user roles correctly', async () => {
    const currentUser = createMockUser('root')
    const permissions = createPermissions('root')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText(/john.doe@example.com/i)).toBeInTheDocument()
    })
    
    // Check that role badges are displayed
    const roleBadges = screen.getAllByText(/^(root|manager|user)$/i)
    expect(roleBadges.length).toBeGreaterThan(0)
  })

  it('displays user status correctly', async () => {
    const currentUser = createMockUser('root')
    const permissions = createPermissions('root')
    
    renderWithProviders(
      <UserManagementPanel currentUser={currentUser} permissions={permissions} />
    )
    
    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText(/john.doe@example.com/i)).toBeInTheDocument()
    })
    
    // Check for status indicators (active/disabled)
    const activeStatuses = screen.getAllByText(/active/i)
    expect(activeStatuses.length).toBeGreaterThan(0)
  })
})