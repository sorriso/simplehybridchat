// path: tests/mocks/data/settings.ts
// version: 1

export interface UserSettings {
  userId: string
  theme: 'light' | 'dark' | 'system'
  promptCustomization: string
  createdAt: Date
  updatedAt: Date
}

export const mockSettings: UserSettings = {
  userId: 'user-john-doe',
  theme: 'system',
  promptCustomization: 'You are a helpful assistant. Be concise and clear.',
  createdAt: new Date('2024-01-01T10:00:00Z'),
  updatedAt: new Date('2024-01-15T14:30:00Z'),
}

export const mockSettingsManager: UserSettings = {
  userId: 'user-manager',
  theme: 'dark',
  promptCustomization: 'You are a professional assistant for team management.',
  createdAt: new Date('2024-01-01T10:00:00Z'),
  updatedAt: new Date('2024-01-10T09:00:00Z'),
}

export const mockSettingsRoot: UserSettings = {
  userId: 'user-root',
  theme: 'light',
  promptCustomization: '',
  createdAt: new Date('2024-01-01T10:00:00Z'),
  updatedAt: new Date('2024-01-01T10:00:00Z'),
}
