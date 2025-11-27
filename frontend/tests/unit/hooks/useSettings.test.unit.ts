// path: tests/unit/hooks/useSettings.test.unit.ts
// version: 4 - Fixed error state timing with waitFor

import { renderHook, act, waitFor } from '@testing-library/react'
import { useSettings } from '@/lib/hooks/useSettings'

// Mock the settings API
jest.mock('@/lib/api/settings', () => ({
  settingsApi: {
    get: jest.fn(),
    update: jest.fn(),
  },
}))

// Import mocked API
import { settingsApi } from '@/lib/api/settings'
const mockSettingsApi = settingsApi as jest.Mocked<typeof settingsApi>

// Mock settings data
const mockSettings = {
  id: 'settings-1',
  userId: 'user-1',
  theme: 'light' as const,
  language: 'en',
  notifications: true,
  fontSize: 'medium' as const,
  autoSave: true,
  promptCustomization: 'Be helpful',
  maxTokens: 4096,
  temperature: 0.7,
  updatedAt: new Date('2024-01-15'),
}

describe('useSettings', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Default: API returns mock settings
    mockSettingsApi.get.mockResolvedValue(mockSettings)
    mockSettingsApi.update.mockResolvedValue(mockSettings)
  })

  describe('Initial state', () => {
    it('starts with loading true and settings null', () => {
      const { result } = renderHook(() => useSettings())
      
      // Initial state before async load completes
      expect(result.current.settings).toBe(null)
      expect(result.current.loading).toBe(true)
      expect(result.current.isSaving).toBe(false)
      expect(result.current.error).toBe(null)
    })
  })

  describe('Load settings', () => {
    it('loads settings successfully on mount', async () => {
      mockSettingsApi.get.mockResolvedValue(mockSettings)
      
      const { result } = renderHook(() => useSettings())
      
      // Wait for loading to complete
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.settings).toEqual(mockSettings)
      expect(result.current.error).toBe(null)
      expect(mockSettingsApi.get).toHaveBeenCalledTimes(1)
    })

    it('handles load error and uses default settings', async () => {
      mockSettingsApi.get.mockRejectedValue(new Error('Load failed'))
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // Error should be set
      expect(result.current.error).toBe('Failed to load settings')
      // Default settings should be used
      expect(result.current.settings).not.toBe(null)
    })

    it('can reload settings', async () => {
      mockSettingsApi.get.mockResolvedValue(mockSettings)
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(mockSettingsApi.get).toHaveBeenCalledTimes(1)
      
      // Update mock to return different settings
      const updatedSettings = { ...mockSettings, theme: 'dark' as const }
      mockSettingsApi.get.mockResolvedValue(updatedSettings)
      
      // Reload
      await act(async () => {
        result.current.reload()
      })
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(mockSettingsApi.get).toHaveBeenCalledTimes(2)
      expect(result.current.settings?.theme).toBe('dark')
    })
  })

  describe('Update settings', () => {
    it('updates settings successfully', async () => {
      const updatedSettings = { ...mockSettings, theme: 'dark' as const }
      mockSettingsApi.get.mockResolvedValue(mockSettings)
      mockSettingsApi.update.mockResolvedValue(updatedSettings)
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.updateSettings({ theme: 'dark' })
      })
      
      expect(mockSettingsApi.update).toHaveBeenCalledWith({ theme: 'dark' })
      expect(result.current.settings?.theme).toBe('dark')
    })

    it('handles update error', async () => {
      mockSettingsApi.get.mockResolvedValue(mockSettings)
      mockSettingsApi.update.mockRejectedValue(new Error('Update failed'))
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // Perform update and expect it to throw
      let threwError = false
      await act(async () => {
        try {
          await result.current.updateSettings({ theme: 'dark' })
        } catch (e) {
          threwError = true
        }
      })
      
      expect(threwError).toBe(true)
      
      // Wait for error state to be set
      await waitFor(() => {
        expect(result.current.error).toBe('Failed to save settings')
      })
    })

    it('sets isSaving during update', async () => {
      let resolveUpdate: (value: typeof mockSettings) => void
      mockSettingsApi.get.mockResolvedValue(mockSettings)
      mockSettingsApi.update.mockImplementation(() => 
        new Promise(resolve => { resolveUpdate = resolve })
      )
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // Start update without awaiting
      let updatePromise: Promise<any>
      act(() => {
        updatePromise = result.current.updateSettings({ theme: 'dark' })
      })
      
      // Should be saving
      expect(result.current.isSaving).toBe(true)
      
      // Resolve the update
      await act(async () => {
        resolveUpdate!(mockSettings)
        await updatePromise
      })
      
      // Should no longer be saving
      expect(result.current.isSaving).toBe(false)
    })

    it('does nothing if settings not loaded', async () => {
      // Make get hang forever to keep settings null
      mockSettingsApi.get.mockImplementation(() => new Promise(() => {}))
      
      const { result } = renderHook(() => useSettings())
      
      // Settings are still null (loading)
      expect(result.current.settings).toBe(null)
      
      // Try to update - should do nothing
      await act(async () => {
        await result.current.updateSettings({ theme: 'dark' })
      })
      
      expect(mockSettingsApi.update).not.toHaveBeenCalled()
    })
  })

  describe('Update theme', () => {
    it('updates theme using convenience method', async () => {
      const updatedSettings = { ...mockSettings, theme: 'dark' as const }
      mockSettingsApi.get.mockResolvedValue(mockSettings)
      mockSettingsApi.update.mockResolvedValue(updatedSettings)
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.updateTheme('dark')
      })
      
      expect(mockSettingsApi.update).toHaveBeenCalledWith({ theme: 'dark' })
      expect(result.current.settings?.theme).toBe('dark')
    })
  })

  describe('Update prompt customization', () => {
    it('updates prompt using convenience method', async () => {
      const newPrompt = 'Be very helpful and concise'
      const updatedSettings = { ...mockSettings, promptCustomization: newPrompt }
      mockSettingsApi.get.mockResolvedValue(mockSettings)
      mockSettingsApi.update.mockResolvedValue(updatedSettings)
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.updatePromptCustomization(newPrompt)
      })
      
      expect(mockSettingsApi.update).toHaveBeenCalledWith({ promptCustomization: newPrompt })
      expect(result.current.settings?.promptCustomization).toBe(newPrompt)
    })
  })

  describe('Multiple updates', () => {
    it('handles sequential updates correctly', async () => {
      mockSettingsApi.get.mockResolvedValue(mockSettings)
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // First update
      const afterTheme = { ...mockSettings, theme: 'dark' as const }
      mockSettingsApi.update.mockResolvedValue(afterTheme)
      
      await act(async () => {
        await result.current.updateTheme('dark')
      })
      
      expect(result.current.settings?.theme).toBe('dark')
      
      // Second update
      const afterPrompt = { ...afterTheme, promptCustomization: 'New prompt' }
      mockSettingsApi.update.mockResolvedValue(afterPrompt)
      
      await act(async () => {
        await result.current.updatePromptCustomization('New prompt')
      })
      
      expect(result.current.settings?.promptCustomization).toBe('New prompt')
      expect(mockSettingsApi.update).toHaveBeenCalledTimes(2)
    })
  })

  describe('Error recovery', () => {
    it('can succeed after previous error', async () => {
      mockSettingsApi.get.mockResolvedValue(mockSettings)
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // First update fails
      mockSettingsApi.update.mockRejectedValueOnce(new Error('Network error'))
      
      await act(async () => {
        try {
          await result.current.updateSettings({ theme: 'dark' })
        } catch (e) {
          // Expected to throw
        }
      })
      
      // Wait for error state
      await waitFor(() => {
        expect(result.current.error).toBe('Failed to save settings')
      })
      
      // Second update succeeds
      const updatedSettings = { ...mockSettings, theme: 'dark' as const }
      mockSettingsApi.update.mockResolvedValue(updatedSettings)
      
      await act(async () => {
        await result.current.updateSettings({ theme: 'dark' })
      })
      
      expect(result.current.error).toBe(null)
      expect(result.current.settings?.theme).toBe('dark')
    })
  })
})