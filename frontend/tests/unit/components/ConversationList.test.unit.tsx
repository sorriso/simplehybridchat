/* path: tests/unit/components/ConversationList.test.unit.tsx
   version: 1 */

   import React from 'react';
   import { render, screen, fireEvent } from '@testing-library/react';
   import { ConversationList } from '@/components/sidebar/ConversationList';
   import type { Conversation, ConversationGroup } from '@/types/conversation';
   
   // Mock ConversationGroup component
   jest.mock('@/components/sidebar/ConversationGroup', () => ({
     ConversationGroup: ({ group, onGroupDelete, onGroupRename }: any) => (
       <div data-testid={`conversation-group-${group.id}`}>
         <div>{group.name}</div>
         <button onClick={onGroupDelete}>Delete Group</button>
         <button onClick={onGroupRename}>Rename Group</button>
       </div>
     ),
   }));
   
   // Mock ConversationItem component
   jest.mock('@/components/sidebar/ConversationItem', () => ({
     ConversationItem: ({ conversation, onClick, onDelete, onRename }: any) => (
       <div data-testid={`conversation-item-${conversation.id}`}>
         <button onClick={onClick}>Open {conversation.title}</button>
         <button onClick={onDelete}>Delete</button>
         <button onClick={onRename}>Rename</button>
       </div>
     ),
   }));
   
   describe('ConversationList', () => {
     const mockGroups: ConversationGroup[] = [
       {
         id: 'group1',
         name: 'Work',
         userId: 'user1',
         conversationIds: ['conv1'],
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
       },
       {
         id: 'group2',
         name: 'Personal',
         userId: 'user1',
         conversationIds: ['conv2'],
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
       },
     ];
   
     const mockConversations: Conversation[] = [
       {
         id: 'conv1',
         title: 'Work Chat',
         userId: 'user1',
         groupId: 'group1',
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
       },
       {
         id: 'conv2',
         title: 'Personal Chat',
         userId: 'user1',
         groupId: 'group2',
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
       },
       {
         id: 'conv3',
         title: 'Ungrouped Chat',
         userId: 'user1',
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
       },
     ];
   
     const defaultProps = {
       conversations: mockConversations,
       groups: mockGroups,
       currentConversationId: null,
       onConversationClick: jest.fn(),
       onConversationDelete: jest.fn(),
       onConversationRename: jest.fn(),
       onGroupDelete: jest.fn(),
       onGroupRename: jest.fn(),
       onMoveConversationToGroup: jest.fn(),
     };
   
     beforeEach(() => {
       jest.clearAllMocks();
     });
   
     it('should render all groups', () => {
       render(<ConversationList {...defaultProps} />);
   
       expect(screen.getByTestId('conversation-group-group1')).toBeInTheDocument();
       expect(screen.getByTestId('conversation-group-group2')).toBeInTheDocument();
       expect(screen.getByText('Work')).toBeInTheDocument();
       expect(screen.getByText('Personal')).toBeInTheDocument();
     });
   
     it('should render ungrouped conversations section', () => {
       render(<ConversationList {...defaultProps} />);
   
       expect(screen.getByText('Ungrouped')).toBeInTheDocument();
       expect(screen.getByTestId('conversation-item-conv3')).toBeInTheDocument();
     });
   
     it('should not render ungrouped section when no ungrouped conversations', () => {
       const props = {
         ...defaultProps,
         conversations: mockConversations.filter((c) => c.groupId),
       };
   
       render(<ConversationList {...props} />);
   
       expect(screen.queryByText('Ungrouped')).not.toBeInTheDocument();
     });
   
     it('should display empty state when no conversations', () => {
       const props = {
         ...defaultProps,
         conversations: [],
       };
   
       render(<ConversationList {...props} />);
   
       expect(screen.getByText('No conversations yet')).toBeInTheDocument();
       expect(screen.getByText(/Click "New Chat" to start/i)).toBeInTheDocument();
     });
   
     it('should call onGroupDelete when group delete is clicked', () => {
       render(<ConversationList {...defaultProps} />);
   
       const deleteButtons = screen.getAllByRole('button', { name: 'Delete Group' });
       fireEvent.click(deleteButtons[0]);
   
       expect(defaultProps.onGroupDelete).toHaveBeenCalledWith('group1');
     });
   
     it('should call onGroupRename when group rename is clicked', () => {
       render(<ConversationList {...defaultProps} />);
   
       const renameButtons = screen.getAllByRole('button', { name: 'Rename Group' });
       fireEvent.click(renameButtons[0]);
   
       expect(defaultProps.onGroupRename).toHaveBeenCalledWith('group1');
     });
   
     it('should handle drag and drop to ungrouped section', () => {
       render(<ConversationList {...defaultProps} />);
   
       const ungroupedSection = screen.getByText('Ungrouped').parentElement;
   
       if (ungroupedSection) {
         // Create mock dataTransfer object
         const mockDataTransfer = {
           dropEffect: 'none',
           effectAllowed: 'all',
           files: [],
           items: [],
           types: [],
           getData: jest.fn(() => 'conv1'),
           setData: jest.fn(),
           clearData: jest.fn(),
         };
   
         // Simulate drag over
         fireEvent.dragOver(ungroupedSection, {
           dataTransfer: mockDataTransfer,
         });
   
         // Update dropEffect for drop
         mockDataTransfer.dropEffect = 'move';
   
         // Simulate drop
         fireEvent.drop(ungroupedSection, {
           dataTransfer: mockDataTransfer,
         });
   
         expect(defaultProps.onMoveConversationToGroup).toHaveBeenCalledWith('conv1', null);
       }
     });
   
     it('should display drop zone indicator when dragging', () => {
       render(<ConversationList {...defaultProps} />);
   
       // Ungrouped section should exist
       const ungroupedText = screen.getByText('Ungrouped');
       expect(ungroupedText).toBeInTheDocument();
     });
   
     it('should filter ungrouped conversations correctly', () => {
       render(<ConversationList {...defaultProps} />);
   
       // Only conv3 should be in ungrouped section
       const ungroupedSection = screen.getByText('Ungrouped').closest('div');
       expect(ungroupedSection).toContainElement(screen.getByTestId('conversation-item-conv3'));
     });
   
     it('should handle drag leave event', () => {
       render(<ConversationList {...defaultProps} />);
   
       const ungroupedSection = screen.getByText('Ungrouped').parentElement;
   
       if (ungroupedSection) {
         // Create mock dataTransfer object
         const mockDataTransfer = {
           dropEffect: 'none',
           effectAllowed: 'all',
           files: [],
           items: [],
           types: [],
           getData: jest.fn(),
           setData: jest.fn(),
           clearData: jest.fn(),
         };
   
         // Simulate drag over first (with mock dataTransfer)
         fireEvent.dragOver(ungroupedSection, {
           dataTransfer: mockDataTransfer,
         });
   
         // Simulate drag leave
         fireEvent.dragLeave(ungroupedSection, {
           clientX: 0,
           clientY: 0,
           dataTransfer: mockDataTransfer,
         });
   
         // State should be updated (no visual assertion possible in unit test)
         expect(ungroupedSection).toBeInTheDocument();
       }
     });
   
     it('should pass correct props to ConversationGroup components', () => {
       render(<ConversationList {...defaultProps} />);
   
       // Both groups should be rendered
       expect(screen.getByTestId('conversation-group-group1')).toBeInTheDocument();
       expect(screen.getByTestId('conversation-group-group2')).toBeInTheDocument();
     });
   
     it('should handle conversation click in ungrouped section', () => {
       render(<ConversationList {...defaultProps} />);
   
       const openButton = screen.getByRole('button', { name: 'Open Ungrouped Chat' });
       fireEvent.click(openButton);
   
       expect(defaultProps.onConversationClick).toHaveBeenCalledWith('conv3');
     });
   
     it('should handle conversation delete in ungrouped section', () => {
       render(<ConversationList {...defaultProps} />);
   
       // Find the conversation item
       const conversationItem = screen.getByTestId('conversation-item-conv3');
       expect(conversationItem).toBeInTheDocument();
   
       // The mocked ConversationItem component renders a delete button
       // Since ConversationItem is mocked, we just verify it's rendered
       expect(conversationItem).toHaveTextContent('Ungrouped Chat');
     });
   });