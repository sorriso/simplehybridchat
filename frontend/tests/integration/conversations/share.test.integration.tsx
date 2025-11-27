// path: tests/integration/conversations/share.test.integration.tsx
// version: 2

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/tests/helpers/render'
import { ShareConversationModal } from '@/components/sharing/ShareConversationModal'

const mockConversation = {
  id: 'conv-1',
  title: 'Test Conversation',
  createdAt: new Date(),
  updatedAt: new Date(),
  messageCount: 5,
  ownerId: 'user-1',
  sharedWithGroupIds: [],
  isShared: false,
}

const mockGroups = [
  {
    id: 'group-1',
    name: 'Engineering Team',
    memberIds: ['user-1', 'user-2'],
    managerIds: ['user-1'],
    status: 'active' as const,
    createdAt: new Date(),
    updatedAt: new Date(),
  },
  {
    id: 'group-2',
    name: 'Marketing Team',
    memberIds: ['user-3', 'user-4'],
    managerIds: ['user-3'],
    status: 'active' as const,
    createdAt: new Date(),
    updatedAt: new Date(),
  },
]

describe('Share Conversation Integration', () => {
  it('displays available groups', async () => {
    renderWithProviders(
      <ShareConversationModal 
        conversation={mockConversation} 
        isOpen={true}
        onClose={jest.fn()}
        availableGroups={mockGroups}
        onShare={jest.fn()}
        onUnshare={jest.fn()}
      />
    )
    
    await waitFor(() => {
      expect(screen.getByText(/engineering team/i)).toBeInTheDocument()
      expect(screen.getByText(/marketing team/i)).toBeInTheDocument()
    })
  })

  it('selects and unselects groups', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(
      <ShareConversationModal 
        conversation={mockConversation} 
        isOpen={true}
        onClose={jest.fn()}
        availableGroups={mockGroups}
        onShare={jest.fn()}
        onUnshare={jest.fn()}
      />
    )
    
    // Find checkbox by the group name in the label
    const engineeringLabel = screen.getByText(/engineering team/i).closest('label')!
    const checkbox = engineeringLabel.querySelector('input[type="checkbox"]') as HTMLInputElement
    
    await user.click(checkbox)
    expect(checkbox).toBeChecked()
    
    await user.click(checkbox)
    expect(checkbox).not.toBeChecked()
  })

  it('saves share settings', async () => {
    const user = userEvent.setup()
    const onShare = jest.fn().mockResolvedValue(undefined)
    const onClose = jest.fn()
    
    renderWithProviders(
      <ShareConversationModal 
        conversation={mockConversation} 
        isOpen={true}
        onClose={onClose}
        availableGroups={mockGroups}
        onShare={onShare}
        onUnshare={jest.fn()}
      />
    )
    
    // Select a group
    const engineeringLabel = screen.getByText(/engineering team/i).closest('label')!
    const checkbox = engineeringLabel.querySelector('input[type="checkbox"]') as HTMLInputElement
    await user.click(checkbox)
    
    // Click save button
    const saveButton = screen.getByRole('button', { name: /save changes/i })
    await user.click(saveButton)
    
    await waitFor(() => {
      expect(onShare).toHaveBeenCalledWith(['group-1'])
      expect(onClose).toHaveBeenCalled()
    })
  })
})