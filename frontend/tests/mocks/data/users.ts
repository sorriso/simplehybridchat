// path: tests/mocks/data/users.ts
// version: 2

export interface User {
  id: string
  name: string
  email: string
  role: 'user' | 'manager' | 'root'
  status: 'active' | 'disabled'
  groupIds: string[]
  createdAt: Date
  updatedAt?: Date
  lastLogin?: Date
}

export interface UserGroup {
  id: string
  name: string
  status: 'active' | 'disabled'
  createdAt: Date
  updatedAt?: Date
  managerIds: string[]
  memberIds: string[]
}

export interface ServerAuthConfig {
  mode: 'none' | 'local' | 'sso'
  allowMultiLogin: boolean
  maintenanceMode: boolean
  ssoConfig?: {
    tokenHeader: string
    nameHeader: string
    emailHeader: string
  }
}

export const mockServerConfig: ServerAuthConfig = {
  mode: 'local',
  allowMultiLogin: false,
  maintenanceMode: false,
}

export const mockUsers: User[] = [
  {
    id: 'user-generic',
    name: 'John Doe',
    email: 'generic@example.com',
    role: 'user',
    status: 'active',
    groupIds: [],
    createdAt: new Date('2024-01-01'),
    lastLogin: new Date('2024-01-15'),
  },
  {
    id: 'user-john-doe',
    name: 'John Doe',
    email: 'john.doe@example.com',
    role: 'user',
    status: 'active',
    groupIds: ['ugroup-1'],
    createdAt: new Date('2024-01-01'),
    lastLogin: new Date('2024-01-15'),
  },
  {
    id: 'user-manager',
    name: 'Jane Manager',
    email: 'jane.manager@example.com',
    role: 'manager',
    status: 'active',
    groupIds: ['ugroup-1', 'ugroup-2'],
    createdAt: new Date('2024-01-01'),
    lastLogin: new Date('2024-01-15'),
  },
  {
    id: 'user-root',
    name: 'Admin Root',
    email: 'admin@example.com',
    role: 'root',
    status: 'active',
    groupIds: [],
    createdAt: new Date('2024-01-01'),
    lastLogin: new Date('2024-01-15'),
  },
  {
    id: 'user-disabled',
    name: 'Disabled User',
    email: 'disabled@example.com',
    role: 'user',
    status: 'disabled',
    groupIds: [],
    createdAt: new Date('2024-01-01'),
    lastLogin: new Date('2024-01-10'),
  },
]

export const mockUserGroups: UserGroup[] = [
  {
    id: 'ugroup-1',
    name: 'Engineering Team',
    status: 'active',
    createdAt: new Date('2024-01-01'),
    managerIds: ['user-manager'],
    memberIds: ['user-john-doe', 'user-manager'],
  },
  {
    id: 'ugroup-2',
    name: 'Marketing Team',
    status: 'active',
    createdAt: new Date('2024-01-01'),
    managerIds: ['user-manager'],
    memberIds: ['user-manager'],
  },
  {
    id: 'ugroup-disabled',
    name: 'Disabled Team',
    status: 'disabled',
    createdAt: new Date('2024-01-01'),
    managerIds: [],
    memberIds: [],
  },
]