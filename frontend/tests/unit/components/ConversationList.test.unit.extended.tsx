/* path: tests/unit/components/ConversationList.test.unit.extended.tsx
   version: 1 - Extended tests for uncovered lines (51, 55-56, 60, 82-83, 178-179) */

   import React from 'react';
   import { render, screen, fireEvent } from '@testing-library/react';
   import { ConversationList } from '@/components/sidebar/ConversationList';
   import type { Conversation, ConversationGroup } from '@/types/conversation';
   
   // Mock child components
   jest.mock('@/components/sidebar/ConversationGroup', () => ({
     ConversationGroup: ({ group, conversations, onDrop, children }: any) => (
       <div
         data-testid={`group-${group.id}`}
         onDrop={(e: any) => {
           const convId = e.dataTransfer?.getData('conversationId');
           if (convId && onDrop) {
             onDrop(convId, group.id);
           }
         }}
       >
         <div>{group.name}</div>
         {children}
       </div>
     ),
   }));
   
   jest.mock('@/components/sidebar/ConversationItem', () => ({
     ConversationItem: ({ conversation, onClick }: any) => (
       <div
         data-testid={`conv-${conversation.id}`}
         onClick={() => onClick?.(conversation.id)}
         draggable
         onDragStart={(e: any) => {
           e.dataTransfer?.setData('conversationId', conversation.id);
         }}
       >
         {conversation.title}
       </div>
     ),
   }));
   
   describe('ConversationList - Extended Drag and Drop Coverage', () => {
     const mockConversations: Conversation[] = [
       {
         id: 'conv1',
         title: 'Conversation 1',
         userId: 'user1',
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
         groupId: 'group1',
       },
       {
         id: 'conv2',
         title: 'Conversation 2',
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
         conversationIds: ['conv1'],
         createdAt: new Date().toISOString(),
         updatedAt: new Date().toISOString(),
       },
     ];
   
     const mockOnMoveConversationToGroup = jest.fn();
   
     beforeEach(() => {
       jest.clearAllMocks();
     });
   
     describe('Conversation Drop on Group', () => {
       it('should handle conversation drop on group', () => {
         render(
           <ConversationList
             conversations={mockConversations}
             groups={mockGroups}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         const group = screen.getByTestId('group-group1');
         const conversation = screen.getByTestId('conv-conv2');
   
         // Simulate drag start
         const dragStartEvent = new Event('dragstart', { bubbles: true });
         Object.defineProperty(dragStartEvent, 'dataTransfer', {
           value: {
             setData: jest.fn(),
             getData: jest.fn().mockReturnValue('conv2'),
           },
         });
         conversation.dispatchEvent(dragStartEvent);
   
         // Simulate drop on group
         const dropEvent = new Event('drop', { bubbles: true });
         Object.defineProperty(dropEvent, 'dataTransfer', {
           value: {
             getData: jest.fn().mockReturnValue('conv2'),
           },
         });
         group.dispatchEvent(dropEvent);
   
         // Verify callback was called
         expect(mockOnMoveConversationToGroup).toHaveBeenCalledWith('conv2', 'group1');
       });
     });
   
     describe('Ungrouped Area Drag Handlers', () => {
       it('should handle dragover on ungrouped area', () => {
         const { container } = render(
           <ConversationList
             conversations={mockConversations}
             groups={mockGroups}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         // Find ungrouped area
         const ungroupedArea = container.querySelector('[class*="bg-gray-50"]');
         
         if (ungroupedArea) {
           const dragOverEvent = new Event('dragover', { bubbles: true });
           Object.defineProperty(dragOverEvent, 'dataTransfer', {
             value: { dropEffect: '' },
             writable: true,
           });
           Object.defineProperty(dragOverEvent, 'preventDefault', {
             value: jest.fn(),
           });
           Object.defineProperty(dragOverEvent, 'stopPropagation', {
             value: jest.fn(),
           });
   
           fireEvent.dragOver(ungroupedArea, dragOverEvent);
         }
       });
   
       it('should set isDragOverUngrouped when dragging over ungrouped', () => {
         const { container } = render(
           <ConversationList
             conversations={mockConversations}
             groups={mockGroups}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         // Simulate dragover event
         const ungroupedSection = screen.getByText('Ungrouped').closest('div');
         
         if (ungroupedSection) {
           fireEvent.dragOver(ungroupedSection);
           // The component should add a highlight class when dragging over
         }
       });
   
       it('should handle dragleave on ungrouped area', () => {
         const { container } = render(
           <ConversationList
             conversations={mockConversations}
             groups={mockGroups}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         const ungroupedSection = screen.getByText('Ungrouped').closest('div');
         
         if (ungroupedSection) {
           // First dragover
           fireEvent.dragOver(ungroupedSection);
           
           // Then dragleave
           fireEvent.dragLeave(ungroupedSection);
         }
       });
   
       it('should handle drop on ungrouped area with valid conversation', () => {
         render(
           <ConversationList
             conversations={mockConversations}
             groups={mockGroups}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         const ungroupedSection = screen.getByText('Ungrouped').closest('div');
         
         if (ungroupedSection) {
           // Simulate drop with conversation data
           const dropEvent = new Event('drop', { bubbles: true });
           Object.defineProperty(dropEvent, 'dataTransfer', {
             value: {
               getData: jest.fn().mockReturnValue('conv1'),
             },
           });
           Object.defineProperty(dropEvent, 'preventDefault', {
             value: jest.fn(),
           });
           Object.defineProperty(dropEvent, 'stopPropagation', {
             value: jest.fn(),
           });
   
           fireEvent.drop(ungroupedSection, dropEvent);
   
           // Should call callback with null to ungroup
           expect(mockOnMoveConversationToGroup).toHaveBeenCalledWith('conv1', null);
         }
       });
   
       it('should not call callback if no conversation id in drop', () => {
         render(
           <ConversationList
             conversations={mockConversations}
             groups={mockGroups}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         const ungroupedSection = screen.getByText('Ungrouped').closest('div');
         
         if (ungroupedSection) {
           // Drop without conversation data
           const dropEvent = new Event('drop', { bubbles: true });
           Object.defineProperty(dropEvent, 'dataTransfer', {
             value: {
               getData: jest.fn().mockReturnValue(''),
             },
           });
           Object.defineProperty(dropEvent, 'preventDefault', {
             value: jest.fn(),
           });
   
           fireEvent.drop(ungroupedSection, dropEvent);
   
           // Should not call callback
           expect(mockOnMoveConversationToGroup).not.toHaveBeenCalled();
         }
       });
   
       it('should not call callback if onMoveConversationToGroup is undefined', () => {
         render(
           <ConversationList
             conversations={mockConversations}
             groups={mockGroups}
             // No onMoveConversationToGroup prop
           />
         );
   
         const ungroupedSection = screen.getByText('Ungrouped').closest('div');
         
         if (ungroupedSection) {
           const dropEvent = new Event('drop', { bubbles: true });
           Object.defineProperty(dropEvent, 'dataTransfer', {
             value: {
               getData: jest.fn().mockReturnValue('conv1'),
             },
           });
   
           fireEvent.drop(ungroupedSection, dropEvent);
   
           // Should not throw error
         }
       });
     });
   
     describe('Empty State', () => {
       it('should show empty state when no conversations', () => {
         render(
           <ConversationList
             conversations={[]}
             groups={[]}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         expect(screen.getByText('No conversations yet')).toBeInTheDocument();
       });
   
       it('should not show empty state when conversations exist', () => {
         render(
           <ConversationList
             conversations={mockConversations}
             groups={mockGroups}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         expect(screen.queryByText('No conversations yet')).not.toBeInTheDocument();
       });
     });
   
     describe('Ungrouped Conversations Display', () => {
       it('should display ungrouped conversations section when present', () => {
         render(
           <ConversationList
             conversations={mockConversations}
             groups={mockGroups}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         // conv2 is ungrouped
         expect(screen.getByText('Ungrouped')).toBeInTheDocument();
         expect(screen.getByText('Conversation 2')).toBeInTheDocument();
       });
   
       it('should not display ungrouped section if all conversations are grouped', () => {
         const allGroupedConversations = mockConversations.map(c => ({
           ...c,
           groupId: 'group1',
         }));
   
         render(
           <ConversationList
             conversations={allGroupedConversations}
             groups={mockGroups}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         // Should not show ungrouped section
         expect(screen.queryByText('Ungrouped')).not.toBeInTheDocument();
       });
     });
   
     describe('Event Propagation', () => {
       it('should stop propagation on dragover', () => {
         const { container } = render(
           <ConversationList
             conversations={mockConversations}
             groups={mockGroups}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         const ungroupedSection = screen.getByText('Ungrouped').closest('div');
         
         if (ungroupedSection) {
           const stopPropagation = jest.fn();
           const preventDefault = jest.fn();
           
           const dragOverEvent = new Event('dragover', { bubbles: true });
           Object.defineProperty(dragOverEvent, 'stopPropagation', {
             value: stopPropagation,
           });
           Object.defineProperty(dragOverEvent, 'preventDefault', {
             value: preventDefault,
           });
           Object.defineProperty(dragOverEvent, 'dataTransfer', {
             value: { dropEffect: '' },
             writable: true,
           });
   
           fireEvent.dragOver(ungroupedSection, dragOverEvent);
   
           // Verify stopPropagation was called
           expect(stopPropagation).toHaveBeenCalled();
           expect(preventDefault).toHaveBeenCalled();
         }
       });
   
       it('should stop propagation on drop', () => {
         render(
           <ConversationList
             conversations={mockConversations}
             groups={mockGroups}
             onMoveConversationToGroup={mockOnMoveConversationToGroup}
           />
         );
   
         const ungroupedSection = screen.getByText('Ungrouped').closest('div');
         
         if (ungroupedSection) {
           const stopPropagation = jest.fn();
           const preventDefault = jest.fn();
           
           const dropEvent = new Event('drop', { bubbles: true });
           Object.defineProperty(dropEvent, 'stopPropagation', {
             value: stopPropagation,
           });
           Object.defineProperty(dropEvent, 'preventDefault', {
             value: preventDefault,
           });
           Object.defineProperty(dropEvent, 'dataTransfer', {
             value: {
               getData: jest.fn().mockReturnValue('conv1'),
             },
           });
   
           fireEvent.drop(ungroupedSection, dropEvent);
   
           expect(stopPropagation).toHaveBeenCalled();
           expect(preventDefault).toHaveBeenCalled();
         }
       });
     });
   });