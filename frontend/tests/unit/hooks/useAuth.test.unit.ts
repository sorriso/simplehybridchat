// path: tests/unit/hooks/useAuth.test.unit.ts
// version: 13 - Focus on business logic, skip window.location.reload test (browser API)

import { renderHook, act, waitFor } from '@testing-library/react'
import { useAuth } from '@/lib/hooks/useAuth'

// Mock the API client - this is what authApi uses internally
jest.mock('@/lib/api/client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(public status: number, message: string, public data?: any) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

// Mock storage
jest.mock('@/lib/utils/storage', () => ({
  storage: {
    getAuthToken: jest.fn(),
    setAuthToken: jest.fn(),
    clearAuthToken: jest.fn(),
  },
}))

// Mock permissions
jest.mock('@/lib/utils/permissions', () => ({
  calculatePermissions: jest.fn((user, mode) => ({
    canManageUsers: user?.role === 'manager' || user?.role === 'root',
    canManageGroups: user?.role === 'root',
    canToggleMaintenance: user?.role === 'root',
  })),
}))

// Import mocked modules
import { apiClient } from '@/lib/api/client'
import { storage } from '@/lib/utils/storage'

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>
const mockStorage = storage as jest.Mocked<typeof storage>

// Mock data
const mockUser = {
  id: 'user-1',
  name: 'John Doe',
  email: 'john@example.com',
  role: 'user' as const,
  status: 'active' as const,
  groupIds: [],
  createdAt: new Date(),
}

const mockManagerUser = {
  ...mockUser,
  id: 'user-manager',
  name: 'Jane Manager',
  role: 'manager' as const,
}

const mockRootUser = {
  ...mockUser,
  id: 'user-root',
  name: 'Admin Root',
  role: 'root' as const,
}

const mockDisabledUser = {
  ...mockUser,
  id: 'user-disabled',
  status: 'disabled' as const,
}

describe('useAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockStorage.getAuthToken.mockReturnValue(null)
    
    // Default: local mode config
    mockApiClient.get.mockImplementation(async (endpoint: string) => {
      if (endpoint === '/api/auth/config') {
        return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } }
      }
      throw new Error(`Unexpected endpoint: ${endpoint}`)
    })
  })

  describe('Initial state', () => {
    it('starts with loading true', () => {
      const { result } = renderHook(() => useAuth())
      
      expect(result.current.loading).toBe(true)
      expect(result.current.user).toBe(null)
      expect(result.current.isAuthenticated).toBe(false)
    })

    it('has default auth mode as local', () => {
      const { result } = renderHook(() => useAuth())
      
      expect(result.current.authMode).toBe('local')
    })
  })

  describe('No auth mode', () => {
    it('automatically authenticates with generic user', async () => {
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'none', allowMultiLogin: true, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/generic') {
          return { user: mockUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.authMode).toBe('none')
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })
  })

  describe('Local auth mode', () => {
    it('loads config and stays unauthenticated without token', async () => {
      mockStorage.getAuthToken.mockReturnValue(null)
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.authMode).toBe('local')
      expect(result.current.user).toBe(null)
      expect(result.current.isAuthenticated).toBe(false)
    })

    it('verifies token and authenticates user', async () => {
      mockStorage.getAuthToken.mockReturnValue('valid-token')
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/verify') {
          return { user: mockUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })

    it('clears invalid token', async () => {
      mockStorage.getAuthToken.mockReturnValue('invalid-token')
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/verify') {
          throw new Error('Invalid token')
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(mockStorage.clearAuthToken).toHaveBeenCalled()
      expect(result.current.user).toBe(null)
      expect(result.current.isAuthenticated).toBe(false)
    })
  })

  describe('SSO auth mode', () => {
    it('verifies SSO session automatically', async () => {
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'sso', allowMultiLogin: false, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/sso/verify') {
          return { user: mockUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.authMode).toBe('sso')
      expect(result.current.user).toEqual(mockUser)
    })
  })

  describe('Login', () => {
    it('logs in successfully with valid credentials', async () => {
      mockStorage.getAuthToken.mockReturnValue(null)
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/verify') {
          return { user: mockUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      mockApiClient.post.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/login') {
          return { user: mockUser, token: 'new-token', expiresAt: new Date().toISOString() }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.login('john@example.com', 'password')
      })
      
      expect(mockStorage.setAuthToken).toHaveBeenCalledWith('new-token')
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })

    it('handles login error', async () => {
      mockStorage.getAuthToken.mockReturnValue(null)
      mockApiClient.post.mockRejectedValue(new Error('Invalid credentials'))
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      let threwError = false
      await act(async () => {
        try {
          await result.current.login('wrong@example.com', 'wrongpassword')
        } catch (e) {
          threwError = true
        }
      })
      
      expect(threwError).toBe(true)
      // Wait for error state to be set
      await waitFor(() => {
        expect(result.current.error).toBe('Invalid credentials')
      })
      expect(result.current.isAuthenticated).toBe(false)
    })

    it('throws error when login called in non-local mode', async () => {
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'none', allowMultiLogin: true, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/generic') {
          return { user: mockUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.authMode).toBe('none')
      
      await expect(async () => {
        await act(async () => {
          await result.current.login('user', 'pass')
        })
      }).rejects.toThrow('Login is only available in local auth mode')
    })
  })

  describe('Logout', () => {
    it('clears user and token on logout', async () => {
      mockStorage.getAuthToken.mockReturnValue('valid-token')
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/verify') {
          return { user: mockUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      mockApiClient.post.mockResolvedValue({})
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.user).toEqual(mockUser)
      
      await act(async () => {
        await result.current.logout()
      })
      
      expect(mockStorage.clearAuthToken).toHaveBeenCalled()
      expect(result.current.user).toBe(null)
      expect(result.current.isAuthenticated).toBe(false)
    })
  })

  describe('Force logout', () => {
    it('revokes session and clears auth token', async () => {
      mockStorage.getAuthToken.mockReturnValue('valid-token')
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/verify') {
          return { user: mockUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      mockApiClient.post.mockResolvedValue({})
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // Note: window.location.reload() call is not tested as it's a browser API
      // and causes issues in jsdom test environment
      await act(async () => {
        try {
          await result.current.forceLogout()
        } catch (error) {
          // Ignore jsdom navigation errors from window.location.reload()
        }
      })
      
      // Verify business logic: API call and token cleanup
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/revoke-own-session')
      expect(mockStorage.clearAuthToken).toHaveBeenCalled()
    })
  })

  describe('Maintenance mode', () => {
    it('shows maintenance mode for non-root users', async () => {
      mockStorage.getAuthToken.mockReturnValue(null)
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: true } }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.maintenanceMode).toBe(true)
      expect(result.current.isAuthenticated).toBe(false)
    })

    it('allows root user during maintenance', async () => {
      mockStorage.getAuthToken.mockReturnValue('root-token')
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: true } }
        }
        if (endpoint === '/api/auth/verify') {
          return { user: mockRootUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.maintenanceMode).toBe(true)
      expect(result.current.user?.role).toBe('root')
      expect(result.current.isAuthenticated).toBe(true)
    })
  })

  describe('User roles', () => {
    it('loads regular user with correct permissions', async () => {
      mockStorage.getAuthToken.mockReturnValue('user-token')
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/verify') {
          return { user: mockUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.user?.role).toBe('user')
      expect(result.current.permissions.canManageUsers).toBe(false)
      expect(result.current.permissions.canManageGroups).toBe(false)
    })

    it('loads manager user with correct permissions', async () => {
      mockStorage.getAuthToken.mockReturnValue('manager-token')
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/verify') {
          return { user: mockManagerUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.user?.role).toBe('manager')
      expect(result.current.permissions.canManageUsers).toBe(true)
    })

    it('loads root user with full permissions', async () => {
      mockStorage.getAuthToken.mockReturnValue('root-token')
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/verify') {
          return { user: mockRootUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.user?.role).toBe('root')
      expect(result.current.permissions.canManageUsers).toBe(true)
      expect(result.current.permissions.canManageGroups).toBe(true)
      expect(result.current.permissions.canToggleMaintenance).toBe(true)
    })
  })

  describe('Disabled user', () => {
    it('marks disabled user as not authenticated', async () => {
      mockStorage.getAuthToken.mockReturnValue('disabled-token')
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/verify') {
          return { user: mockDisabledUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.user?.status).toBe('disabled')
      expect(result.current.isAuthenticated).toBe(false)
    })
  })

  describe('Reload', () => {
    it('reloads auth state', async () => {
      mockStorage.getAuthToken.mockReturnValue(null)
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.user).toBe(null)
      
      // Update mock for reload
      mockStorage.getAuthToken.mockReturnValue('new-token')
      mockApiClient.get.mockImplementation(async (endpoint: string) => {
        if (endpoint === '/api/auth/config') {
          return { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } }
        }
        if (endpoint === '/api/auth/verify') {
          return { user: mockUser }
        }
        throw new Error(`Unexpected endpoint: ${endpoint}`)
      })
      
      act(() => {
        result.current.reload()
      })
      
      await waitFor(() => {
        expect(result.current.user).toEqual(mockUser)
      })
    })
  })

  describe('Error handling', () => {
    it('handles config load error', async () => {
      mockApiClient.get.mockRejectedValue(new Error('Network error'))
      
      const { result } = renderHook(() => useAuth())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.error).toBe('Network error')
    })
  })
})