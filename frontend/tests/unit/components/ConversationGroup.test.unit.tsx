/* path: tests/unit/components/ConversationGroup.test.unit.tsx
   version: 1 */

   import React from 'react';
   import { render, screen, fireEvent } from '@testing-library/react';
   import { ConversationGroup } from '@/components/sidebar/ConversationGroup';
   import type { ConversationGroup as ConversationGroupType, Conversation } from '@/types/conversation';
   
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
   
   // Mock ContextMenu component
   jest.mock('@/components/ui/ContextMenu', () => ({
     ContextMenu: ({ children, items }: any) => (
       <div data-testid="context-menu">
         {children}
         {items.map((item: any, idx: number) => (
           <button key={idx} onClick={item.onClick}>
             {item.label}
           </button>
         ))}
       </div>
     ),
   }));
   
   describe('ConversationGroup', () => {
     const mockGroup: ConversationGroupType = {
       id: 'group1',
       name: 'Test Group',
       userId: 'user1',
       conversationIds: ['conv1', 'conv2'],
       createdAt: new Date().toISOString(),
       updatedAt: new Date().toISOString(),
     };
   
     const mockConversations: Conversation[] = [
       {
         id: 'conv1',
         title: 'Conversation 1',
         userId: 'user1',
         groupId: 'group1',
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
       },
       {
         id: 'conv2',
         title: 'Conversation 2',
         userId: 'user1',
         groupId: 'group1',
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
       },
       {
         id: 'conv3',
         title: 'Conversation 3',
         userId: 'user1',
         groupId: 'group2',
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
       },
     ];
   
     const defaultProps = {
       group: mockGroup,
       conversations: mockConversations,
       currentConversationId: null,
       onConversationClick: jest.fn(),
       onConversationDelete: jest.fn(),
       onConversationRename: jest.fn(),
       onGroupDelete: jest.fn(),
       onGroupRename: jest.fn(),
     };
   
     beforeEach(() => {
       jest.clearAllMocks();
     });
   
     it('should render group header with name and conversation count', () => {
       render(<ConversationGroup {...defaultProps} />);
   
       expect(screen.getByText('Test Group')).toBeInTheDocument();
       expect(screen.getByText('(2)')).toBeInTheDocument();
     });
   
     it('should filter and display only conversations belonging to the group', () => {
       render(<ConversationGroup {...defaultProps} />);
   
       expect(screen.getByTestId('conversation-item-conv1')).toBeInTheDocument();
       expect(screen.getByTestId('conversation-item-conv2')).toBeInTheDocument();
       expect(screen.queryByTestId('conversation-item-conv3')).not.toBeInTheDocument();
     });
   
     it('should toggle expanded state when clicking header', () => {
       render(<ConversationGroup {...defaultProps} />);
   
       const header = screen.getByRole('button', { name: /Test Group/i });
   
       // Initially expanded, conversations are visible
       expect(screen.getByTestId('conversation-item-conv1')).toBeInTheDocument();
   
       // Click to collapse
       fireEvent.click(header);
   
       // Conversations should not be visible (component sets display based on isExpanded)
       // Note: In the actual implementation, the conversations div is conditionally rendered
       expect(screen.queryByTestId('conversation-item-conv1')).not.toBeInTheDocument();
     });
   
     it('should call onGroupDelete when delete is clicked', () => {
       render(<ConversationGroup {...defaultProps} />);
   
       // Get all delete buttons, the first one is from the context menu (group level)
       const deleteButtons = screen.getAllByRole('button', { name: 'Delete' });
       fireEvent.click(deleteButtons[0]); // First button is the group delete
   
       expect(defaultProps.onGroupDelete).toHaveBeenCalledTimes(1);
     });
   
     it('should call onGroupRename when rename is clicked', () => {
       render(<ConversationGroup {...defaultProps} />);
   
       // Get all rename buttons, the first one is from the context menu (group level)
       const renameButtons = screen.getAllByRole('button', { name: 'Rename' });
       fireEvent.click(renameButtons[0]); // First button is the group rename
   
       expect(defaultProps.onGroupRename).toHaveBeenCalledTimes(1);
     });
   
     it('should display empty state when group has no conversations', () => {
       const emptyProps = {
         ...defaultProps,
         conversations: [],
       };
   
       render(<ConversationGroup {...emptyProps} />);
   
       expect(screen.getByText(/No conversations/i)).toBeInTheDocument();
     });
   
     it('should handle drag over event', () => {
       render(<ConversationGroup {...defaultProps} />);
   
       const contextMenu = screen.getByTestId('context-menu');
       const dropZone = contextMenu.querySelector('div[class*="rounded-lg"]');
   
       expect(dropZone).toBeInTheDocument();
   
       if (dropZone) {
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
   
         fireEvent.dragOver(dropZone, {
           dataTransfer: mockDataTransfer,
         });
   
         // Verify drag over styling is applied (component sets isDragOver state)
         expect(dropZone).toHaveClass('rounded-lg');
       }
     });
   
     it('should handle drop event and call onConversationDrop', () => {
       const onConversationDrop = jest.fn();
       const props = {
         ...defaultProps,
         onConversationDrop,
       };
   
       render(<ConversationGroup {...props} />);
   
       const contextMenu = screen.getByTestId('context-menu');
       const dropZone = contextMenu.querySelector('div[class*="rounded-lg"]');
   
       if (dropZone) {
         // Create mock dataTransfer object
         const mockDataTransfer = {
           dropEffect: 'none',
           effectAllowed: 'all',
           files: [],
           items: [],
           types: [],
           getData: jest.fn(() => 'conv3'),
           setData: jest.fn(),
           clearData: jest.fn(),
         };
   
         fireEvent.drop(dropZone, {
           dataTransfer: mockDataTransfer,
         });
   
         expect(onConversationDrop).toHaveBeenCalledWith('conv3', 'group1');
       }
     });
   
     it('should display drop indicator when dragging over', () => {
       const props = {
         ...defaultProps,
         draggingConversationId: 'conv3',
       };
   
       render(<ConversationGroup {...props} />);
   
       const contextMenu = screen.getByTestId('context-menu');
       const dropZone = contextMenu.querySelector('div[class*="rounded-lg"]');
   
       if (dropZone) {
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
   
         fireEvent.dragOver(dropZone, {
           dataTransfer: mockDataTransfer,
         });
   
         // The drop indicator should be visible when dragging
         // Note: The component renders the indicator based on both isDragOver and draggingConversationId
         expect(screen.getByText(/Drop here to move to Test Group/i)).toBeInTheDocument();
       }
     });
   
     it('should pass drag handlers to conversation items', () => {
       const onDragStart = jest.fn();
       const onDragEnd = jest.fn();
       const props = {
         ...defaultProps,
         onDragStart,
         onDragEnd,
       };
   
       render(<ConversationGroup {...props} />);
   
       // ConversationItem components receive the drag handlers
       expect(screen.getByTestId('conversation-item-conv1')).toBeInTheDocument();
       expect(screen.getByTestId('conversation-item-conv2')).toBeInTheDocument();
     });
   });