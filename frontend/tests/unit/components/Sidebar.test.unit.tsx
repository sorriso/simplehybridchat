/* path: tests/unit/components/Sidebar.test.unit.tsx
   version: 2 - Extended coverage for rename, delete, errors */

   import React from 'react';
   import { render, screen, fireEvent, waitFor } from '@testing-library/react';
   import { Sidebar } from '@/components/sidebar/Sidebar';
   import type { Conversation, ConversationGroup } from '@/types/conversation';
   
   // Mock child components
   jest.mock('@/components/sidebar/NewConversationButton', () => ({
     NewConversationButton: ({ onClick }: any) => (
       <button onClick={onClick}>New Conversation</button>
     ),
   }));
   
   jest.mock('@/components/sidebar/ConversationList', () => ({
     ConversationList: ({ 
       onConversationClick, 
       onConversationDelete,
       onConversationRename,
       onGroupDelete,
       onGroupRename,
       onMoveConversationToGroup 
     }: any) => (
       <div data-testid="conversation-list">
         <button onClick={() => onConversationClick('conv1')}>Click Conv</button>
         <button onClick={() => onConversationDelete?.('conv1')}>Delete Conv</button>
         <button onClick={() => onConversationRename?.('conv1')}>Rename Conv</button>
         <button onClick={() => onGroupDelete?.('group1')}>Delete Group</button>
         <button onClick={() => onGroupRename?.('group1')}>Rename Group</button>
         <button onClick={() => onMoveConversationToGroup?.('conv1', 'group1')}>
           Move to Group
         </button>
         <button onClick={() => onMoveConversationToGroup?.('conv1', null)}>
           Move to Ungrouped
         </button>
       </div>
     ),
   }));
   
   jest.mock('@/components/ui/IconButton', () => ({
     IconButton: ({ icon: Icon, onClick, title }: any) => (
       <button onClick={onClick} title={title}>
         {title}
       </button>
     ),
   }));
   
   jest.mock('@/components/ui/Modal', () => ({
     Modal: ({ isOpen, onClose, title, children }: any) =>
       isOpen ? (
         <div data-testid="modal">
           <h2>{title}</h2>
           {children}
           <button onClick={onClose} data-testid="modal-close">Close Modal</button>
         </div>
       ) : null,
   }));
   
   jest.mock('@/components/ui/Input', () => ({
     Input: ({ value, onChange, label, onKeyDown }: any) => (
       <div>
         <label>{label}</label>
         <input
           value={value}
           onChange={onChange}
           onKeyDown={onKeyDown}
           placeholder={label}
         />
       </div>
     ),
   }));
   
   jest.mock('@/components/ui/Button', () => ({
     Button: ({ children, onClick, disabled, variant }: any) => (
       <button onClick={onClick} disabled={disabled} data-variant={variant}>
         {children}
       </button>
     ),
   }));
   
   // Mock window.confirm
   global.confirm = jest.fn();
   
   describe('Sidebar - Extended Coverage', () => {
     const mockConversations: Conversation[] = [
       {
         id: 'conv1',
         title: 'Conversation 1',
         userId: 'user1',
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
       },
     ];
   
     const mockGroups: ConversationGroup[] = [
       {
         id: 'group1',
         name: 'Group 1',
         userId: 'user1',
         conversationIds: [],
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
       },
     ];
   
     const defaultProps = {
       conversations: mockConversations,
       groups: mockGroups,
       currentConversationId: null,
       createConversation: jest.fn().mockResolvedValue(mockConversations[0]),
       deleteConversation: jest.fn().mockResolvedValue(undefined),
       updateConversation: jest.fn().mockResolvedValue(mockConversations[0]),
       createGroup: jest.fn().mockResolvedValue(mockGroups[0]),
       deleteGroup: jest.fn().mockResolvedValue(undefined),
       setCurrentConversationId: jest.fn(),
       onSettingsClick: jest.fn(),
       onUploadClick: jest.fn(),
     };
   
     beforeEach(() => {
       jest.clearAllMocks();
       (global.confirm as jest.Mock).mockReturnValue(true);
     });
   
     describe('Conversation Rename', () => {
       it('should open rename modal when rename is clicked', () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Rename Conv'));
   
         expect(screen.getByTestId('modal')).toBeInTheDocument();
         expect(screen.getByText('Rename Conversation')).toBeInTheDocument();
         expect(screen.getByPlaceholderText('Conversation Title')).toHaveValue('Conversation 1');
       });
   
       it('should submit rename when Save button is clicked', async () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Rename Conv'));
   
         const input = screen.getByPlaceholderText('Conversation Title');
         fireEvent.change(input, { target: { value: 'New Title' } });
   
         const saveButton = screen.getByRole('button', { name: 'Save' });
         fireEvent.click(saveButton);
   
         await waitFor(() => {
           expect(defaultProps.updateConversation).toHaveBeenCalledWith('conv1', {
             title: 'New Title',
           });
         });
       });
   
       it('should close rename modal after successful rename', async () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Rename Conv'));
   
         const input = screen.getByPlaceholderText('Conversation Title');
         fireEvent.change(input, { target: { value: 'New Title' } });
         fireEvent.click(screen.getByRole('button', { name: 'Save' }));
   
         await waitFor(() => {
           expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
         });
       });
   
       it('should handle rename error gracefully', async () => {
         const consoleError = jest.spyOn(console, 'error').mockImplementation();
         const props = {
           ...defaultProps,
           updateConversation: jest.fn().mockRejectedValue(new Error('Update failed')),
         };
   
         render(<Sidebar {...props} />);
   
         fireEvent.click(screen.getByText('Rename Conv'));
   
         const input = screen.getByPlaceholderText('Conversation Title');
         fireEvent.change(input, { target: { value: 'New Title' } });
         fireEvent.click(screen.getByRole('button', { name: 'Save' }));
   
         await waitFor(() => {
           expect(consoleError).toHaveBeenCalledWith(
             'Failed to rename conversation:',
             expect.any(Error)
           );
         });
   
         consoleError.mockRestore();
       });
   
       it('should not submit rename if title is empty', async () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Rename Conv'));
   
         const input = screen.getByPlaceholderText('Conversation Title');
         fireEvent.change(input, { target: { value: '' } });
   
         const saveButton = screen.getByRole('button', { name: 'Save' });
         fireEvent.click(saveButton);
   
         // Should not be called since title is empty
         expect(defaultProps.updateConversation).not.toHaveBeenCalled();
       });
   
       it('should submit rename on Enter key', async () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Rename Conv'));
   
         const input = screen.getByPlaceholderText('Conversation Title');
         fireEvent.change(input, { target: { value: 'New Title' } });
         fireEvent.keyDown(input, { key: 'Enter' });
   
         await waitFor(() => {
           expect(defaultProps.updateConversation).toHaveBeenCalledWith('conv1', {
             title: 'New Title',
           });
         });
       });
   
       it('should close modal on Cancel button', () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Rename Conv'));
         expect(screen.getByTestId('modal')).toBeInTheDocument();
   
         const cancelButton = screen.getByRole('button', { name: 'Cancel' });
         fireEvent.click(cancelButton);
   
         expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
       });
     });
   
     describe('Group Rename', () => {
       it('should open rename group modal when rename is clicked', () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Rename Group'));
   
         expect(screen.getByTestId('modal')).toBeInTheDocument();
         // There are two "Rename Group" texts: button and modal title
         const renameTexts = screen.getAllByText('Rename Group');
         expect(renameTexts.length).toBeGreaterThanOrEqual(1);
         expect(screen.getByPlaceholderText('Group Name')).toHaveValue('Group 1');
       });
   
       it('should close modal on Cancel button', () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Rename Group'));
         expect(screen.getByTestId('modal')).toBeInTheDocument();
   
         const cancelButton = screen.getByRole('button', { name: 'Cancel' });
         fireEvent.click(cancelButton);
   
         expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
       });
     });
   
     describe('Conversation Delete', () => {
       it('should delete conversation when confirmed', async () => {
         (global.confirm as jest.Mock).mockReturnValue(true);
   
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Delete Conv'));
   
         await waitFor(() => {
           expect(global.confirm).toHaveBeenCalledWith(
             'Are you sure you want to delete this conversation?'
           );
           expect(defaultProps.deleteConversation).toHaveBeenCalledWith('conv1');
         });
       });
   
       it('should not delete conversation when cancelled', async () => {
         (global.confirm as jest.Mock).mockReturnValue(false);
   
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Delete Conv'));
   
         await waitFor(() => {
           expect(global.confirm).toHaveBeenCalled();
         });
   
         expect(defaultProps.deleteConversation).not.toHaveBeenCalled();
       });
   
       it('should handle delete error gracefully', async () => {
         (global.confirm as jest.Mock).mockReturnValue(true);
         const consoleError = jest.spyOn(console, 'error').mockImplementation();
         const props = {
           ...defaultProps,
           deleteConversation: jest.fn().mockRejectedValue(new Error('Delete failed')),
         };
   
         render(<Sidebar {...props} />);
   
         fireEvent.click(screen.getByText('Delete Conv'));
   
         await waitFor(() => {
           expect(consoleError).toHaveBeenCalledWith(
             'Failed to delete conversation:',
             expect.any(Error)
           );
         });
   
         consoleError.mockRestore();
       });
     });
   
     describe('Group Delete', () => {
       it('should delete group when confirmed', async () => {
         (global.confirm as jest.Mock).mockReturnValue(true);
   
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Delete Group'));
   
         await waitFor(() => {
           expect(global.confirm).toHaveBeenCalledWith(
             'Are you sure you want to delete this group? Conversations will not be deleted.'
           );
           expect(defaultProps.deleteGroup).toHaveBeenCalledWith('group1');
         });
       });
   
       it('should not delete group when cancelled', async () => {
         (global.confirm as jest.Mock).mockReturnValue(false);
   
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Delete Group'));
   
         await waitFor(() => {
           expect(global.confirm).toHaveBeenCalled();
         });
   
         expect(defaultProps.deleteGroup).not.toHaveBeenCalled();
       });
   
       it('should handle delete group error gracefully', async () => {
         (global.confirm as jest.Mock).mockReturnValue(true);
         const consoleError = jest.spyOn(console, 'error').mockImplementation();
         const props = {
           ...defaultProps,
           deleteGroup: jest.fn().mockRejectedValue(new Error('Delete failed')),
         };
   
         render(<Sidebar {...props} />);
   
         fireEvent.click(screen.getByText('Delete Group'));
   
         await waitFor(() => {
           expect(consoleError).toHaveBeenCalledWith(
             'Failed to delete group:',
             expect.any(Error)
           );
         });
   
         consoleError.mockRestore();
       });
     });
   
     describe('Move Conversation', () => {
       it('should move conversation to group', async () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Move to Group'));
   
         await waitFor(() => {
           expect(defaultProps.updateConversation).toHaveBeenCalledWith('conv1', {
             groupId: 'group1',
           });
         });
       });
   
       it('should move conversation to ungrouped (null)', async () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByText('Move to Ungrouped'));
   
         await waitFor(() => {
           expect(defaultProps.updateConversation).toHaveBeenCalledWith('conv1', {
             groupId: undefined,
           });
         });
       });
   
       it('should handle move error gracefully', async () => {
         const consoleError = jest.spyOn(console, 'error').mockImplementation();
         const props = {
           ...defaultProps,
           updateConversation: jest.fn().mockRejectedValue(new Error('Move failed')),
         };
   
         render(<Sidebar {...props} />);
   
         fireEvent.click(screen.getByText('Move to Group'));
   
         await waitFor(() => {
           expect(consoleError).toHaveBeenCalledWith(
             'Failed to move conversation:',
             expect.any(Error)
           );
         });
   
         consoleError.mockRestore();
       });
     });
   
     describe('New Group Modal', () => {
       it('should close modal with Cancel button', () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByTitle('New Group'));
         expect(screen.getByTestId('modal')).toBeInTheDocument();
   
         const cancelButton = screen.getByRole('button', { name: 'Cancel' });
         fireEvent.click(cancelButton);
   
         expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
       });
   
       it('should close modal with X button', () => {
         render(<Sidebar {...defaultProps} />);
   
         fireEvent.click(screen.getByTitle('New Group'));
         expect(screen.getByTestId('modal')).toBeInTheDocument();
   
         const closeButton = screen.getByTestId('modal-close');
         fireEvent.click(closeButton);
   
         expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
       });
     });
   });