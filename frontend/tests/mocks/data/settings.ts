// path: tests/mocks/data/settings.ts
// version: 2

export interface UserSettings {
  id: string
  userId: string
  theme: 'light' | 'dark' | 'auto'
  language: string
  notifications: boolean
  fontSize: 'small' | 'medium' | 'large'
  autoSave: boolean
  customPrompt: string | null
  promptCustomization: string
  maxTokens: number
  temperature: number
  updatedAt: Date
}

export const mockSettings: UserSettings = {
  id: 'settings-1',
  userId: 'user-john-doe',
  theme: 'light',
  language: 'en',
  notifications: true,
  fontSize: 'medium',
  autoSave: true,
  customPrompt: null,
  promptCustomization: 'You are a helpful assistant. Be concise and clear.',
  maxTokens: 4096,
  temperature: 0.7,
  updatedAt: new Date('2024-01-15T14:30:00Z'),
}

export const mockSettingsManager: UserSettings = {
  id: 'settings-2',
  userId: 'user-manager',
  theme: 'dark',
  language: 'en',
  notifications: true,
  fontSize: 'medium',
  autoSave: true,
  customPrompt: null,
  promptCustomization: 'You are a professional assistant for team management.',
  maxTokens: 4096,
  temperature: 0.7,
  updatedAt: new Date('2024-01-10T09:00:00Z'),
}