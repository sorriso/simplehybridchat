// path: tests/mocks/data/files.ts
// version: 1

export interface MockFile {
    id: string
    name: string
    size: number
    mimeType: string
    url: string
    uploadedAt: string
    status: 'pending' | 'uploading' | 'completed' | 'error'
    userId: string
    conversationId: string | null
  }
  
  export const mockFiles: MockFile[] = [
    {
      id: 'file-1',
      name: 'document.pdf',
      size: 1024 * 100, // 100KB
      mimeType: 'application/pdf',
      url: '/uploads/document.pdf',
      uploadedAt: '2024-01-15T10:00:00Z',
      status: 'completed',
      userId: 'user-john-doe',
      conversationId: 'conv-1',
    },
    {
      id: 'file-2',
      name: 'image.png',
      size: 1024 * 500, // 500KB
      mimeType: 'image/png',
      url: '/uploads/image.png',
      uploadedAt: '2024-01-15T11:00:00Z',
      status: 'completed',
      userId: 'user-john-doe',
      conversationId: 'conv-1',
    },
    {
      id: 'file-3',
      name: 'notes.txt',
      size: 1024, // 1KB
      mimeType: 'text/plain',
      url: '/uploads/notes.txt',
      uploadedAt: '2024-01-15T12:00:00Z',
      status: 'completed',
      userId: 'user-john-doe',
      conversationId: null,
    },
    {
      id: 'file-4',
      name: 'spreadsheet.xlsx',
      size: 1024 * 200, // 200KB
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      url: '/uploads/spreadsheet.xlsx',
      uploadedAt: '2024-01-14T09:00:00Z',
      status: 'completed',
      userId: 'user-manager',
      conversationId: 'conv-2',
    },
  ]